from __future__ import annotations

from pathlib import Path

from onec_hbk_bsl.analysis.diagnostics import DiagnosticEngine


def _single_diag(content: str, code: str, tmp_path: Path, **engine_kwargs):
    path = tmp_path / "Module.bsl"
    path.write_text(content, encoding="utf-8")
    diags = DiagnosticEngine(select={code}, **engine_kwargs).check_file(str(path))
    assert diags, f"expected at least one {code} diagnostic"
    return diags[0]


def test_bsl014_uses_full_line_span_from_column_zero(tmp_path: Path) -> None:
    diag = _single_diag("А = \"" + ("x" * 130) + "\";\n", "BSL014", tmp_path)
    assert diag.character == 0
    assert diag.end_character > 120


def test_bsl011_attaches_to_method_name_span(tmp_path: Path) -> None:
    content = """\
Функция ОченьСложнаяФункция(Знач А, Знач Б, Знач В) Экспорт
    Если А Тогда
        Если Б Тогда
            Если В Тогда
                Возврат 1;
            ИначеЕсли А Тогда
                Возврат 2;
            Иначе
                Возврат 3;
            КонецЕсли;
        Иначе
            Возврат 4;
        КонецЕсли;
    ИначеЕсли Б Тогда
        Возврат 5;
    Иначе
        Возврат 6;
    КонецЕсли;
КонецФункции
"""
    diag = _single_diag(content, "BSL011", tmp_path, max_cognitive_complexity=1)
    header = content.splitlines()[0]
    start = header.index("ОченьСложнаяФункция")
    assert diag.character == start
    assert diag.end_character == start + len("ОченьСложнаяФункция")


def test_bsl019_attaches_to_method_name_span(tmp_path: Path) -> None:
    content = """\
Функция СложнаяФункция(Знач А, Знач Б, Знач В) Экспорт
    Если А Тогда
        Возврат 1;
    КонецЕсли;
    Если Б Тогда
        Возврат 2;
    КонецЕсли;
    Если В Тогда
        Возврат 3;
    КонецЕсли;
    Для Каждого Элемент Из Новый Массив Цикл
        Если Элемент = Неопределено Тогда
            Возврат 4;
        КонецЕсли;
    КонецЦикла;
    Возврат 0;
КонецФункции
"""
    diag = _single_diag(content, "BSL019", tmp_path, max_mccabe_complexity=1)
    header = content.splitlines()[0]
    start = header.index("СложнаяФункция")
    assert diag.character == start
    assert diag.end_character == start + len("СложнаяФункция")
