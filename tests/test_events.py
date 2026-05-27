import unittest

from codex_nock.config import PrivacyConfig
from codex_nock.events import build_notification, infer_status, redact


class EventTests(unittest.TestCase):
    def test_minimal_notification_does_not_include_message(self):
        event = {"type": "agent-turn-complete", "message": "secret prompt text"}
        notification = build_notification(event, PrivacyConfig(mode="minimal"), "demo")

        self.assertIn("Status: completed", notification.body)
        self.assertIn("Project: demo", notification.body)
        self.assertNotIn("secret prompt text", notification.body)

    def test_summary_mode_redacts_tokens(self):
        event = {"type": "done", "message": "token=abc123 and sk-abcdefghijklmnop"}
        notification = build_notification(event, PrivacyConfig(mode="summary"), "demo")

        self.assertIn("[redacted]", notification.body)
        self.assertNotIn("abc123", notification.body)
        self.assertNotIn("sk-abcdefghijklmnop", notification.body)

    def test_infer_approval_status(self):
        self.assertEqual(infer_status({"type": "PermissionRequest"}), "needs-approval")

    def test_redact_custom_pattern(self):
        self.assertEqual(redact("pin 1234", [r"\d+"]), "pin [redacted]")


if __name__ == "__main__":
    unittest.main()
