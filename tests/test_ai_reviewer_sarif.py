#!/usr/bin/env python3
"""Tests for SARIF output format in ai_reviewer."""
import json
import sys
import os
from pathlib import Path

# Add parent to path so we can import ai_reviewer
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.ai_reviewer import (
    AiCodeReviewer,
    ReviewSeverity,
    ReviewCategory,
    ReviewFinding,
    ProjectReviewReport,
    FileReviewResult,
    ComplexityMetrics,
    QualityScore,
    generate_sarif_report,
    _map_severity_to_sarif_level,
)


# ---------------------------------------------------------------------------
# Sample fixture data
# ---------------------------------------------------------------------------

SAMPLE_CRITICAL_FILE = """
import os
import sys

password = "supersecret1234567890"

def login(user, password):
    result = os.system("echo " + user)
    return result
"""

SAMPLE_WARNING_FILE = """
def highly_complex_function(a, b, c, d, e, f):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            return "nested too deep"
    return "ok"
"""

SAMPLE_INFO_FILE = """
# a short file
x = 1
y = 2
"""


def _run_review_on_source(source: str, filename: str = "test_sample.py") -> FileReviewResult:
    """Run the AI reviewer on an in-memory source file."""
    tmp_dir = Path("/tmp/test_fixtures")
    tmp_dir.mkdir(exist_ok=True)
    file_path = tmp_dir / filename
    file_path.write_text(source)
    try:
        reviewer = AiCodeReviewer()
        return reviewer.review_file(file_path)
    finally:
        file_path.unlink(missing_ok=True)


def test_severity_mapping():
    """Verify severity-to-SARIF-level mapping is consistent."""
    assert _map_severity_to_sarif_level(ReviewSeverity.CRITICAL) == "error"
    assert _map_severity_to_sarif_level(ReviewSeverity.ERROR) == "error"
    assert _map_severity_to_sarif_level(ReviewSeverity.WARNING) == "warning"
    assert _map_severity_to_sarif_level(ReviewSeverity.INFO) == "note"
    assert _map_severity_to_sarif_level(ReviewSeverity.SUGGESTION) == "note"


def test_critical_severity_finding_produces_sarif_error_level():
    """A CRITICAL security finding should map to SARIF 'error' level."""
    result = _run_review_on_source(SAMPLE_CRITICAL_FILE)
    report = ProjectReviewReport(
        timestamp="2024-01-01T00:00:00",
        project_path="/tmp/test_fixtures/test_sample.py",
        total_files=1,
        reviewed_files=1,
        total_findings=len(result.findings),
        critical_findings=len([f for f in result.findings if f.severity == ReviewSeverity.CRITICAL]),
        errors=len([f for f in result.findings if f.severity == ReviewSeverity.ERROR]),
        warnings=len([f for f in result.findings if f.severity == ReviewSeverity.WARNING]),
        info_findings=len([f for f in result.findings if f.severity == ReviewSeverity.INFO]),
        suggestions=len([f for f in result.findings if f.severity == ReviewSeverity.SUGGESTION]),
        file_results=[result],
    )

    sarif = json.loads(generate_sarif_report(report))

    # Verify SARIF structure
    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert len(sarif["runs"]) == 1
    assert sarif["runs"][0]["tool"]["driver"]["name"] == "ai-reviewer"

    # Verify at least one CRITICAL-level result maps to "error"
    results = sarif["runs"][0]["results"]
    assert len(results) > 0

    # Check that hardcoded secrets (CRITICAL) produce error level
    critical_results = [r for r in results if r["level"] == "error"]
    assert len(critical_results) > 0
    print(f"  CRITICAL results mapping to error: {len(critical_results)}")


def test_sarif_output_contains_required_fields():
    """Verify SARIF output includes file path, line number, rule id, message."""
    result = _run_review_on_source(SAMPLE_CRITICAL_FILE)
    report = ProjectReviewReport(
        timestamp="2024-01-01T00:00:00",
        project_path="/tmp/test_fixtures/test_sample.py",
        total_files=1,
        reviewed_files=1,
        total_findings=len(result.findings),
        critical_findings=len([f for f in result.findings if f.severity == ReviewSeverity.CRITICAL]),
        errors=len([f for f in result.findings if f.severity == ReviewSeverity.ERROR]),
        warnings=len([f for f in result.findings if f.severity == ReviewSeverity.WARNING]),
        info_findings=len([f for f in result.findings if f.severity == ReviewSeverity.INFO]),
        suggestions=len([f for f in result.findings if f.severity == ReviewSeverity.SUGGESTION]),
        file_results=[result],
    )

    sarif = json.loads(generate_sarif_report(report))
    results = sarif["runs"][0]["results"]

    for r in results:
        # Must have ruleId
        assert "ruleId" in r, f"Missing ruleId in result: {r}"
        # Must have message
        assert "message" in r, f"Missing message in result: {r}"
        assert "text" in r["message"], f"Missing message.text in result: {r}"
        # Must have locations with file path and line number
        assert "locations" in r, f"Missing locations in result: {r}"
        assert len(r["locations"]) > 0
        loc = r["locations"][0]
        assert "physicalLocation" in loc
        assert "artifactLocation" in loc["physicalLocation"]
        assert "uri" in loc["physicalLocation"]["artifactLocation"]
        assert "region" in loc["physicalLocation"]
        assert "startLine" in loc["physicalLocation"]["region"]


def test_sarif_deterministic():
    """Verify SARIF output is deterministic (same source = same SARIF)."""
    result1 = _run_review_on_source(SAMPLE_INFO_FILE, "test1.py")
    result2 = _run_review_on_source(SAMPLE_INFO_FILE, "test2.py")

    report1 = ProjectReviewReport(
        timestamp="2024-01-01T00:00:00",
        project_path="/tmp/test_fixtures/test1.py",
        total_files=1,
        reviewed_files=1,
        total_findings=len(result1.findings),
        critical_findings=0,
        errors=0,
        warnings=0,
        info_findings=len(result1.findings),
        suggestions=0,
        file_results=[result1],
    )
    report2 = ProjectReviewReport(
        timestamp="2024-01-01T00:00:00",
        project_path="/tmp/test_fixtures/test2.py",
        total_files=1,
        reviewed_files=1,
        total_findings=len(result2.findings),
        critical_findings=0,
        errors=0,
        warnings=0,
        info_findings=len(result2.findings),
        suggestions=0,
        file_results=[result2],
    )

    sarif1 = json.loads(generate_sarif_report(report1))
    sarif2 = json.loads(generate_sarif_report(report2))

    # Both should have same number of results for same file
    assert len(sarif1["runs"][0]["results"]) == len(sarif2["runs"][0]["results"])


def test_no_findings_produces_empty_results():
    """A report with no findings should produce an empty results array."""
    report = ProjectReviewReport(
        timestamp="2024-01-01T00:00:00",
        project_path="/tmp/empty",
        total_files=1,
        reviewed_files=1,
        total_findings=0,
        critical_findings=0,
        errors=0,
        warnings=0,
        info_findings=0,
        suggestions=0,
        file_results=[
            FileReviewResult(
                file_path="/tmp/empty/clean.py",
                language="python",
                line_count=1,
                findings=[],
            )
        ],
    )

    sarif = json.loads(generate_sarif_report(report))
    assert sarif["runs"][0]["results"] == []


def test_warning_and_note_levels():
    """Verify WARNING maps to 'warning' and INFO/SUGGESTION to 'note'."""
    result = _run_review_on_source(SAMPLE_WARNING_FILE)
    report = ProjectReviewReport(
        timestamp="2024-01-01T00:00:00",
        project_path="/tmp/test_fixtures/test_sample.py",
        total_files=1,
        reviewed_files=1,
        total_findings=len(result.findings),
        critical_findings=0,
        errors=0,
        warnings=len([f for f in result.findings if f.severity == ReviewSeverity.WARNING]),
        info_findings=len([f for f in result.findings if f.severity == ReviewSeverity.INFO]),
        suggestions=0,
        file_results=[result],
    )

    sarif = json.loads(generate_sarif_report(report))
    results = sarif["runs"][0]["results"]

    levels_seen = {r["level"] for r in results}
    # Should have at least 'warning' level from complexity warnings
    assert "warning" in levels_seen, f"No 'warning' level found in levels: {levels_seen}"


if __name__ == "__main__":
    tests = [
        test_severity_mapping,
        test_critical_severity_finding_produces_sarif_error_level,
        test_sarif_output_contains_required_fields,
        test_sarif_deterministic,
        test_no_findings_produces_empty_results,
        test_warning_and_note_levels,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
