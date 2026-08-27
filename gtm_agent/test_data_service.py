import unittest

from . import data_service


def rebuild_profile(prospect_id):
    existing = data_service.get_profile_from_db(prospect_id)["prospect_profile"]
    if existing is not None:
        return existing
    record = data_service.get_prospect_record(prospect_id)
    profile = {
        "prospect_id": prospect_id,
        **record,
        "engagement_history": data_service.fetch_engagement_history(prospect_id),
        "account_details": data_service.fetch_account_details(prospect_id),
        "tech_stack": data_service.fetch_tech_stack(prospect_id),
    }
    data_service.save_profile_to_db(prospect_id, profile)
    return profile


class UpdateProspectInfoTest(unittest.TestCase):
    def test_update_persists_to_source_and_rebuilt_profile(self):
        prospect_id = "LEAD-71001"
        record = data_service.PROSPECTS[prospect_id]
        original_stack = list(record["tech_stack"])
        data_service._PROFILES.pop(prospect_id, None)
        try:
            stale_profile = rebuild_profile(prospect_id)
            self.assertNotIn("Kafka", stale_profile["tech_stack"])

            result = data_service.update_prospect_info(prospect_id, "Kafka")
            profile = rebuild_profile(prospect_id)

            self.assertTrue(result["updated"])
            self.assertIn("Kafka", data_service.fetch_tech_stack(prospect_id))
            self.assertIn("Kafka", profile["tech_stack"])
        finally:
            record["tech_stack"] = original_stack
            data_service._PROFILES.pop(prospect_id, None)


if __name__ == "__main__":
    unittest.main()
