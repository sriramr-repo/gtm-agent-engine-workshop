import json
import os
import sys
import types
from pathlib import Path


package = types.ModuleType("gtm_agent")
package.__path__ = [str(Path(__file__).parent)]
sys.modules["gtm_agent"] = package
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from gtm_agent import data_service
from gtm_agent.gtm_agent import (
    ProspectScore,
    _scoring_llm,
    build_prospect_profile,
    get_prospect,
    score_prospect,
)


SENSITIVE_KEYS = {
    "tax_id", "date_of_birth", "card_on_file", "credit_check_ref",
    "billing_qualification",
}


def _keys(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(item) for item in value))
    return set()


def test_prospect_tools_exclude_billing_fields(monkeypatch):
    data_service._PROFILES.clear()
    captured = {}

    def fake_invoke(_self, messages):
        captured["messages"] = messages
        return ProspectScore(
            score=85,
            justification="Good fit.",
            rubric_breakdown={
                "revenue_fit": 100,
                "tech_stack_match": 75,
                "segment_fit": 100,
            },
        )

    monkeypatch.setattr(type(_scoring_llm), "invoke", fake_invoke)

    contact = get_prospect.invoke({"prospect_id": "LEAD-71001"})
    profile = build_prospect_profile.invoke({"prospect_id": "LEAD-71001"})
    score = score_prospect.invoke({
        "prospect_profile": profile["prospect_profile"],
        "offering": {
            "required_tech_stack": ["Snowflake"],
            "min_annual_revenue": 1,
            "description": "Test offering",
            "target_segment": "Enterprise",
        },
    })

    assert not SENSITIVE_KEYS.intersection(_keys(contact))
    assert not SENSITIVE_KEYS.intersection(_keys(profile))
    assert not SENSITIVE_KEYS.intersection(_keys(score))
    assert not SENSITIVE_KEYS.intersection(_keys(captured["messages"]))
    assert not any(key in json.dumps(captured["messages"]) for key in SENSITIVE_KEYS)
