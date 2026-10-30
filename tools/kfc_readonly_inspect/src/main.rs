//! Minimal read-only KFC resource inspector.
//!
//! The tool uses only KFCReader/File::open paths from pinned kfc-parser. It
//! never imports a writer, patches resources, or writes inside the game tree.

use anyhow::{bail, Context, Result};
use kfc::{
    container::KFCReader,
    guid::ResourceId,
    reflection::{LookupKey, TypeRegistry},
    resource::value::{ConversionOptions, Value},
};
use serde_json::json;
use std::{env, fs, path::{Path, PathBuf}};

const PINNED_REV: &str = "16708594d686b030d909f2d835b199d879ea9ad8";

fn inside(path: &Path, root: &Path) -> bool {
    path.starts_with(root)
}

fn run() -> Result<()> {
    let args: Vec<_> = env::args_os().collect();
    if args.len() < 4 || args.len() > 5 {
        bail!("usage: kfc-readonly-inspect <game-dir> <guid> <qualified-type> [output.json]");
    }
    let game_dir = PathBuf::from(&args[1]).canonicalize()
        .context("game directory is unavailable")?;
    let executable = game_dir.join("enshrouded.exe");
    let registry = TypeRegistry::load_from_executable(&executable)
        .context("cannot load reflection from executable")?;
    let type_name = args[3].to_string_lossy();
    let metadata = registry.get_by_name(LookupKey::Qualified(&type_name))
        .with_context(|| format!("type not found: {type_name}"))?;
    let guid_text = args[2].to_string_lossy();
    let id = ResourceId::parse(&guid_text, metadata.qualified_hash, 0)
        .with_context(|| format!("invalid GUID: {guid_text}"))?;

    let reader = KFCReader::new(&game_dir, "enshrouded")
        .context("cannot open KFC inputs")?;
    let mut cursor = reader.new_cursor().context("cannot open KFC resource cursor")?;
    let bytes = cursor.read_resource(&id).context("cannot read resource")?
        .context("resource not found")?;
    let value = Value::from_bytes_with_options(
        &registry, metadata, &bytes, ConversionOptions::HUMAN_READABLE,
    ).context("cannot decode resource")?;
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
        let output = PathBuf::from(output);
        let parent = output.parent().context("output has no parent")?.canonicalize()
            .context("output parent is unavailable")?;
        if inside(&parent, &game_dir) {
            bail!("refusing to write inside game directory");
        }
        if output.exists() {
            bail!("refusing to overwrite output");
        }
        fs::write(&output, encoded).context("cannot write report")?;
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
