"""BSL150 BadWords — BSLLS default empty pattern; optional regex via engine."""

from __future__ import annotations

from onec_hbk_bsl.analysis.diagnostics import DiagnosticEngine


def test_bsl150_default_pattern_emits_nothing() -> None:
    engine = DiagnosticEngine(select={"BSL150"})
    src = "// foo\nПроцедура Тест() КонецПроцедуры\n"
    diags = engine.check_content("m.bsl", src)
    assert [d.code for d in diags] == []


def test_bsl150_with_pattern_finds_word() -> None:
    engine = DiagnosticEngine(
        select={"BSL150"},
        bad_words_pattern=r"BADWORD",
    )
    src = "Процедура Тест() // BADWORD here\nКонецПроцедуры\n"
    diags = engine.check_content("m.bsl", src)
    assert len(diags) == 1
    assert diags[0].code == "BSL150"
    assert diags[0].line == 1
