//! Minimal read-only KFC resource inspector.
//!
//! The tool uses only KFCReader/File::open paths from pinned kfc-parser. It
//! never imports a writer, patches resources, or writes inside the game tree.

use anyhow::{Context, Result, bail};
use kfc::{
    container::KFCReader,
    guid::ResourceId,
    reflection::{LookupKey, TypeRegistry},
    resource::value::{ConversionOptions, Value},
};
use serde_json::json;
use std::{
    env,
    fs::{self, File, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
};

const PINNED_REV: &str = "16708594d686b030d909f2d835b199d879ea9ad8";

fn inside(path: &Path, root: &Path) -> bool {
    path.starts_with(root)
}

fn output_path(raw: &Path, game_dir: &Path) -> Result<PathBuf> {
    let raw = if raw.is_absolute() {
        raw.to_path_buf()
    } else {
        env::current_dir()
            .context("current directory is unavailable")?
            .join(raw)
    };
    let parent = raw
        .parent()
        .context("output has no parent")?
        .canonicalize()
        .context("output parent is unavailable")?;
    let output = parent.join(raw.file_name().context("output has no file name")?);
    if inside(&output, game_dir) {
        bail!("refusing to write inside game directory");
    }
    if output.exists() {
        bail!("refusing to overwrite output");
    }
    Ok(output)
}

fn write_new(output: &Path, encoded: &[u8]) -> Result<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(output)
        .context("cannot create new report")?;
    let result = file
        .write_all(encoded)
        .and_then(|_| file.flush())
        .and_then(|_| file.sync_all());
    if let Err(error) = result {
        drop(file);
        let _ = fs::remove_file(output);
        return Err(error).context("cannot finalize report");
    }
    Ok(())
}

fn npc_id(value: &serde_json::Value) -> Result<Option<u32>> {
    let components = value.get("components").and_then(|v| v.as_array())
        .context("template components are unavailable")?;
    let mut found = None;
    for component in components {
        if component.get("$type").and_then(|v| v.as_str()) == Some("keen::ecs::ActiveNpcState") {
            if found.is_some() { bail!("duplicate ActiveNpcState"); }
            let id = component.pointer("/$value/npcId/value").and_then(|v| v.as_u64())
                .context("invalid typed npcId")?;
            found = Some(u32::try_from(id).context("npcId exceeds UInt32")?);
        }
    }
    Ok(found)
}

fn audit(reader: &KFCReader, registry: &TypeRegistry, game: &Path, wanted: u32) -> Result<serde_json::Value> {
    let file = reader.file();
    let mut containers = Vec::new();
    for (index, info) in file.containers().iter().enumerate() {
        let name = format!("enshrouded_{index:03}.dat");
        let size = fs::metadata(game.join(&name))?.len();
        if size != info.size { bail!("container size mismatch: {name}"); }
        containers.push(json!({"path":name,"bytes":size,"entries":info.count}));
    }
    for entry in file.contents().values() {
        let container = file.containers().get(entry.container_index)
            .context("content references absent container")?;
        if entry.offset >= container.size { bail!("content offset outside container"); }
    }
    let resources_size = fs::metadata(game.join("enshrouded.kfc_resources"))?.len();
    for chunk in file.resource_chunks() {
        if chunk.offset.checked_add(chunk.compressed_size).context("chunk overflow")? > resources_size {
            bail!("resource chunk outside resources file");
        }
    }
    let mut unique_ids = std::collections::HashSet::new();
    for id in file.resources().keys() {
        if !unique_ids.insert((id.guid().to_string(), id.type_hash(), id.part_index())) {
            bail!("duplicate resource identity");
        }
    }
    let metadata = registry.get_by_name(LookupKey::Qualified("keen::ecs::TemplateResource"))
        .context("TemplateResource schema missing")?;
    let mut cursor = reader.new_cursor()?;
    let mut count = 0;
    let mut npc_templates = 0;
    let mut collisions = Vec::new();
    for id in file.resources_by_type(metadata.qualified_hash) {
        let bytes = cursor.read_resource(id)?.context("indexed template missing")?;
        let value = Value::from_bytes_with_options(registry, metadata, &bytes, ConversionOptions::HUMAN_READABLE)?;
        let serialized = serde_json::to_value(value)?;
        if let Some(npc) = npc_id(&serialized)? {
            npc_templates += 1;
            if npc == wanted { collisions.push(id.guid().to_string()); }
        }
        count += 1;
    }
    Ok(json!({"mode":"READ_ONLY_DATABASE_AUDIT", "pinned_kfc_parser":PINNED_REV,
        "version":file.game_version(), "container_count":containers.len(), "containers":containers,
        "content_references_checked":file.contents().len(), "resource_index_count":file.resources().len(),
        "resource_chunks_checked":file.resource_chunks().len(), "duplicate_resource_ids":0,
        "templates_decoded":count, "npc_templates":npc_templates, "requested_npc_id":wanted,
        "npc_collisions":collisions, "runtime_status":"NOT_EXECUTED", "spawn_ready":false}))
}

fn run() -> Result<()> {
    let args: Vec<_> = env::args_os().collect();
    if args.len() < 4 || args.len() > 5 {
        bail!(
            "usage: kfc-readonly-inspect [--list-type|--lookup-guid|--audit] <game-dir> <guid|qualified-type|npc-id> [qualified-type|output.json] [output.json]"
        );
    }
    let list_type = args[1] == "--list-type";
    let lookup_guid = args[1] == "--lookup-guid";
    let database_audit = args[1] == "--audit";
    let game_arg = if list_type || lookup_guid || database_audit {
        &args[2]
    } else {
        &args[1]
    };
    let game_dir = PathBuf::from(game_arg)
        .canonicalize()
        .context("game directory is unavailable")?;
    let executable = game_dir.join("enshrouded.exe");
    let kfc = game_dir.join("enshrouded.kfc");
    let resources = game_dir.join("enshrouded.kfc_resources");
    for input in [&executable, &kfc, &resources] {
        let resolved = input
            .canonicalize()
            .context("required input is unavailable")?;
        File::open(&resolved).context("required input is not readable")?;
    }
    let registry = TypeRegistry::load_from_executable(&executable)
        .context("cannot load reflection from executable")?;
    let reader = KFCReader::new(&game_dir, "enshrouded").context("cannot open KFC inputs")?;
    if database_audit {
        let wanted: u32 = args[3].to_string_lossy().parse().context("npc-id must be UInt32")?;
        let report = audit(&reader, &registry, &game_dir, wanted)?;
        let encoded = serde_json::to_vec_pretty(&report)?;
        if let Some(output) = args.get(4) {
            write_new(&output_path(&PathBuf::from(output), &game_dir)?, &encoded)?;
        } else {
            println!("{}", String::from_utf8(encoded)?);
        }
        return Ok(());
    }
    if lookup_guid {
        let guid_text = args[3].to_string_lossy();
        let resources: Vec<_> = reader
            .file()
            .resources()
            .keys()
            .iter()
            .filter(|id| id.guid().to_string().eq_ignore_ascii_case(&guid_text))
            .map(|id| {
                let type_name = registry
                    .get_by_hash(LookupKey::Qualified(id.type_hash()))
                    .map(|value| value.qualified_name.as_str());
                json!({
                    "guid": id.guid().to_string(), "part": id.part_index(),
                    "type_hash": format!("{:08x}", id.type_hash()), "type": type_name,
                })
            })
            .collect();
        let report = json!({
            "mode": "READ_ONLY_GUID_LOOKUP", "pinned_kfc_parser": PINNED_REV,
            "guid": guid_text, "count": resources.len(), "resources": resources,
        });
        let encoded = serde_json::to_vec_pretty(&report)?;
        if let Some(output) = args.get(4) {
            let output = output_path(&PathBuf::from(output), &game_dir)?;
            write_new(&output, &encoded)?;
        } else {
            println!("{}", String::from_utf8(encoded)?);
        }
        return Ok(());
    }
    let type_name = args[3].to_string_lossy();
    let metadata = registry
        .get_by_name(LookupKey::Qualified(&type_name))
        .with_context(|| format!("type not found: {type_name}"))?;
    if list_type {
        let resources: Vec<_> = reader
            .file()
            .resources_by_type(metadata.qualified_hash)
            .map(|id| json!({"guid": id.guid().to_string(), "part": id.part_index()}))
            .collect();
        let report = json!({
            "mode": "READ_ONLY_TYPE_INDEX",
            "pinned_kfc_parser": PINNED_REV,
            "type": type_name,
            "count": resources.len(),
            "resources": resources,
        });
        let encoded = serde_json::to_vec_pretty(&report)?;
        if let Some(output) = args.get(4) {
            let output = output_path(&PathBuf::from(output), &game_dir)?;
            write_new(&output, &encoded)?;
        } else {
            println!("{}", String::from_utf8(encoded)?);
        }
        return Ok(());
    }
    let guid_text = args[2].to_string_lossy();
    let id = ResourceId::parse(&guid_text, metadata.qualified_hash, 0)
        .with_context(|| format!("invalid GUID: {guid_text}"))?;

    let mut cursor = reader
        .new_cursor()
        .context("cannot open KFC resource cursor")?;
    let bytes = cursor
        .read_resource(&id)
        .context("cannot read resource")?
        .context("resource not found")?;
    let value = Value::from_bytes_with_options(
        &registry,
        metadata,
        &bytes,
        ConversionOptions::HUMAN_READABLE,
    )
    .context("cannot decode resource")?;
    let report = json!({
        "mode": "READ_ONLY",
        "pinned_kfc_parser": PINNED_REV,
        "guid": guid_text,
        "type": type_name,
        "part": 0,
        "resource": value,
    });
    let encoded = serde_json::to_vec_pretty(&report)?;
    if let Some(output) = args.get(4) {
        let output = output_path(&PathBuf::from(output), &game_dir)?;
        write_new(&output, &encoded)?;
    } else {
        println!("{}", String::from_utf8(encoded)?);
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error:#}");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn sandbox() -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = env::temp_dir().join(format!("aic-kfc-inspector-{nonce}"));
        fs::create_dir(&path).unwrap();
        path.canonicalize().unwrap()
    }

    #[test]
    fn output_inside_game_is_rejected() {
        let game = sandbox();
        let error = output_path(&game.join("report.json"), &game).unwrap_err();
        assert!(error.to_string().contains("inside game directory"));
        fs::remove_dir(&game).unwrap();
    }

    #[test]
    fn create_new_never_overwrites_existing_report() {
        let root = sandbox();
        let report = root.join("report.json");
        write_new(&report, b"first").unwrap();
        assert!(write_new(&report, b"second").is_err());
        assert_eq!(fs::read(&report).unwrap(), b"first");
        fs::remove_file(report).unwrap();
        fs::remove_dir(root).unwrap();
    }

    #[test]
    fn collision_scan_requires_typed_unsigned_npc_id() {
        assert_eq!(npc_id(&json!({"components":[]})).unwrap(), None);
        let component = json!({"$type":"keen::ecs::ActiveNpcState","$value":{"npcId":{"value":2939921867u32}}});
        assert_eq!(npc_id(&json!({"components":[component.clone()]})).unwrap(), Some(2939921867));
        assert!(npc_id(&json!({"components":[component.clone(),component]})).is_err());
        for bad in [json!(-1), json!(4294967296u64), json!("123"), json!(true), json!(null)] {
            assert!(npc_id(&json!({"components":[{"$type":"keen::ecs::ActiveNpcState","$value":{"npcId":{"value":bad}}}]})).is_err());
        }
        assert!(npc_id(&json!({})).is_err());
    }
}
