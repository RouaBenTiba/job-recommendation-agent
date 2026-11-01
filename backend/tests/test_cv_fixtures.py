"""The fictional CVs used by scripts/evaluate_profile_extraction.py must stay consistent."""

import json
from pathlib import Path

import pytest

from app.services.text_cleaning import clean_text

FIXTURES = Path(__file__).parent / "fixtures" / "cvs"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))


def test_every_fixture_has_expectations_and_vice_versa() -> None:
    files = {path.name for path in FIXTURES.glob("*.txt")}
    assert files == set(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_expected_facts_are_really_in_the_cv(name: str) -> None:
    text = clean_text((FIXTURES / name).read_text(encoding="utf-8")).casefold()
    spec = EXPECTED[name]
    for key in ("technologies", "companies", "schools", "forbidden"):
        for item in spec[key]:
            assert item.casefold() in text, f"{name}: '{item}' ({key}) is not in the CV"
