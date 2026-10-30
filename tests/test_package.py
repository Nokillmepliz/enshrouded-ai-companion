import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_archive_excludes_runtime_and_is_disabled(self):
        spec = importlib.util.spec_from_file_location('aic_package', ROOT / 'scripts/package.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            target = module.build(Path(folder) / 'body.zip')
            with ZipFile(target) as archive:
                self.assertEqual(set(archive.namelist()),
                                 {'aic_body/' + name for name in module.FILES})
                self.assertFalse(json.loads(archive.read('aic_body/mod.json'))['enabled'])
            first = target.read_bytes()
            module.build(target)
            self.assertEqual(first, target.read_bytes())
