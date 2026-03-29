"""BSL113 AssignmentInCondition — registry parity; valid BSL uses ``=`` as comparison in ``Если``."""

from __future__ import annotations

from onec_hbk_bsl.analysis.diagnostics import DiagnosticEngine


def test_bsl113_is_no_op_for_valid_bsl() -> None:
    src = (
        'Процедура Тест()\n'
        '    Если А = 1 Тогда\n'
        '    КонецЕсли;\n'
        "КонецПроцедуры\n"
    )
    engine = DiagnosticEngine(select={"BSL113"})
    diags = engine.check_content("m.bsl", src)
    assert diags == []
