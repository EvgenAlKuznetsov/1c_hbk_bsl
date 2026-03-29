"""BSL148 AllFunctionPathMustHaveReturn — BSLLS fixture parity (default loop option)."""

from __future__ import annotations

from pathlib import Path

import pytest

from onec_hbk_bsl.analysis.diagnostics import DiagnosticEngine

_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "diag_bslls"
    / "AllFunctionPathMustHaveReturnDiagnostic.bsl"
)


@pytest.mark.skipif(not _FIXTURE.is_file(), reason="copy from BSLLS diagnostics resources")
def test_bsl148_matches_bslls_default_fixture() -> None:
    engine = DiagnosticEngine(select={"BSL148"})
    diags = [d for d in engine.check_file(str(_FIXTURE)) if d.code == "BSL148"]
    lines = sorted({d.line for d in diags})
    assert lines == [1, 26, 94, 103, 132]


@pytest.mark.skipif(not _FIXTURE.is_file(), reason="copy from BSLLS diagnostics resources")
def test_bsl148_loops_false_adds_for_loop_case() -> None:
    engine = DiagnosticEngine(
        select={"BSL148"},
        bsl148_loops_executed_at_least_once=False,
    )
    diags = [d for d in engine.check_file(str(_FIXTURE)) if d.code == "BSL148"]
    lines = sorted({d.line for d in diags})
    assert lines == [1, 26, 37, 94, 103, 132]
