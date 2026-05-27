import tempfile
import unittest
from pathlib import Path

from codex_nock.setup import CODEX_NOTIFY_LINE, apply_desktop_setup, upsert_top_level_notify


class SetupTests(unittest.TestCase):
    def test_insert_notify_before_first_section(self):
        content = 'model = "gpt-5.5"\n\n[features]\nmulti_agent = true\n'
        updated = upsert_top_level_notify(content)

        self.assertIn(CODEX_NOTIFY_LINE, updated.splitlines()[:3])
        self.assertLess(updated.index(CODEX_NOTIFY_LINE), updated.index("[features]"))

    def test_replace_existing_top_level_notify(self):
        content = 'notify = ["old"]\nmodel = "gpt-5.5"\n'
        updated = upsert_top_level_notify(content)

        self.assertIn(CODEX_NOTIFY_LINE, updated)
        self.assertNotIn('notify = ["old"]', updated)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nock = root / "nock.toml"
            codex = root / "config.toml"

            result = apply_desktop_setup(nock, codex, dry_run=True)

            self.assertTrue(result.nock_config_changed)
            self.assertTrue(result.codex_config_changed)
            self.assertFalse(nock.exists())
            self.assertFalse(codex.exists())

    def test_setup_writes_files_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nock = root / "nock.toml"
            codex = root / "config.toml"
            codex.write_text('model = "gpt-5.5"\n', encoding="utf-8")

            result = apply_desktop_setup(nock, codex, project_name="Demo")

            self.assertTrue(nock.exists())
            self.assertIn('provider = "desktop"', nock.read_text(encoding="utf-8"))
            self.assertIn('project_name = "Demo"', nock.read_text(encoding="utf-8"))
            self.assertIn(CODEX_NOTIFY_LINE, codex.read_text(encoding="utf-8"))
            self.assertIsNotNone(result.codex_backup_path)
            self.assertTrue(result.codex_backup_path.exists())

    def test_setup_backs_up_existing_nock_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nock = root / "nock.toml"
            codex = root / "config.toml"
            nock.write_text('[notify]\nprovider = "stdout"\n', encoding="utf-8")

            result = apply_desktop_setup(nock, codex, project_name="Demo")

            self.assertIsNotNone(result.nock_backup_path)
            self.assertTrue(result.nock_backup_path.exists())
            self.assertIn('provider = "stdout"', result.nock_backup_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
