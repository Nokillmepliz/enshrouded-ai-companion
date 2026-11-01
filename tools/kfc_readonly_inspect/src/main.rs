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

fn run() -> Result<()> {
    let args: Vec<_> = env::args_os().collect();
    if args.len() < 4 || args.len() > 5 {
        bail!(
            "usage: kfc-readonly-inspect [--list-type|--lookup-guid] <game-dir> <guid|qualified-type> [qualified-type|output.json] [output.json]"
        );
    }
    let list_type = args[1] == "--list-type";
    let lookup_guid = args[1] == "--lookup-guid";
    let game_arg = if list_type || lookup_guid {
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
}
