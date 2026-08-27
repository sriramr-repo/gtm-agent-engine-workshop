import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch

source_dir = str(Path(__file__).resolve().parents[1])
sys.path = [path for path in sys.path if path not in ("", source_dir)]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent.gtm_agent import send_prospect_email


def call_send(prospect_id, *, confirmed_override=False):
    return send_prospect_email.func(
        prospect={"prospect_id": prospect_id, "name": "Test Prospect", "email": "test@example.com"},
        subject="Test subject",
        body="Test body",
        runtime=None,
        from_rep={"name": "Test Rep", "email": "rep@example.com"},
        confirmed_override=confirmed_override,
    )


class SendProspectEmailTests(unittest.TestCase):
    def test_disqualified_prospect_is_blocked_without_sending(self):
        with patch("gtm_agent.gtm_agent.uuid.uuid4") as uuid4:
            result = call_send("LEAD-50001")

        self.assertEqual(result, {
            "status": "blocked",
            "reason": "prospect is disqualified",
            "requires_confirmation": True,
        })
        uuid4.assert_not_called()

    def test_disqualified_prospect_sends_with_confirmed_override(self):
        result = call_send("LEAD-50001", confirmed_override=True)

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["to"], "test@example.com")

    def test_non_disqualified_prospect_sends_normally(self):
        result = call_send("LEAD-15229")

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["to"], "test@example.com")


if __name__ == "__main__":
    unittest.main()
