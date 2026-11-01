"""Manual evaluation of the profile extraction on the fictional CVs (US-4.3, task 5).

Calls the REAL Gemini API with the key from backend/.env: never run it in CI.
Only fictional CVs are used. Run it from backend/:

    python scripts/evaluate_profile_extraction.py --list-models
    python scripts/evaluate_profile_extraction.py
    python scripts/evaluate_profile_extraction.py --min-recall 0.9
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google import genai  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.schemas.profile import ProfileUpdate  # noqa: E402
from app.services.llm.base import LLMError  # noqa: E402
from app.services.llm.gemini import build_gemini_client  # noqa: E402
from app.services.profile_extraction import ProfileExtractionError, extract_profile  # noqa: E402
from app.services.text_cleaning import clean_text  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "cvs"


def list_models() -> int:
    settings = get_settings()
    if settings.gemini_api_key is None:
        print("GEMINI_API_KEY is not set in backend/.env")
        return 1
    client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())
    print(f"Configured model (GEMINI_MODEL): {settings.gemini_model}")
    print("Models your key can use for generateContent:")
    for model in client.models.list():
        if "generateContent" in (model.supported_actions or []):
            print(f"  - {(model.name or '').removeprefix('models/')}")
    return 0


def missing(expected: list[str], found: list[str]) -> list[str]:
    lowered = [value.casefold() for value in found]
    return [e for e in expected if not any(e.casefold() in v or v in e.casefold() for v in lowered)]


def evaluate(min_recall: float) -> int:
    expected = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
    settings = get_settings()
    try:
        llm = build_gemini_client()
    except LLMError as exc:
        print(f"Cannot start: {exc}")
        return 1
    print(f"Model: {llm.model}\n")

    hits = total = 0
    failed = False
    for name, spec in sorted(expected.items()):
        text = clean_text((FIXTURES / name).read_text(encoding="utf-8"))
        try:
            profile: ProfileUpdate = extract_profile(llm, text, max_attempts=settings.llm_max_attempts)
        except (ProfileExtractionError, LLMError) as exc:
            print(f"{name}: FAILED ({type(exc).__name__}: {exc})")
            failed = True
            continue

        experiences = profile.experiences or []
        found_tech = [*(profile.technologies or []), *(profile.skills or [])]
        for exp in experiences:
            found_tech.extend(exp.technologies)
        miss_tech = missing(spec["technologies"], found_tech)
        miss_companies = missing(spec["companies"], [e.company for e in experiences])
        miss_schools = missing(spec["schools"], [e.school for e in profile.education or []])
        dump = profile.model_dump_json().casefold()
        leaks = [item for item in spec["forbidden"] if item.casefold() in dump]
        too_many = len(experiences) > spec["max_experiences"]

        expected_count = len(spec["technologies"]) + len(spec["companies"]) + len(spec["schools"])
        missed_count = len(miss_tech) + len(miss_companies) + len(miss_schools)
        hits += expected_count - missed_count
        total += expected_count

        print(f"{name} ({spec['language']}): found {expected_count - missed_count}/{expected_count}")
        for label, items in (("technologies", miss_tech), ("companies", miss_companies), ("schools", miss_schools)):
            if items:
                print(f"    missing {label}: {', '.join(items)}")
        if leaks:
            print(f"    CONTACT DETAILS LEAKED: {', '.join(leaks)}")
            failed = True
        if too_many:
            print(f"    INVENTED EXPERIENCES: {len(experiences)} (max {spec['max_experiences']})")
            failed = True

    recall = hits / total if total else 0.0
    print(f"\nOverall recall: {recall:.0%} (threshold {min_recall:.0%})")
    if recall < min_recall:
        failed = True
    print("RESULT:", "FAILED" if failed else "OK")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list-models", action="store_true", help="list the models your API key can use")
    parser.add_argument("--min-recall", type=float, default=0.8, help="minimum share of expected facts found")
    args = parser.parse_args()
    return list_models() if args.list_models else evaluate(args.min_recall)


if __name__ == "__main__":
    raise SystemExit(main())
