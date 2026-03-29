"""BSL158–BSL160 common-module rules (metadata + XML layout)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from onec_hbk_bsl.analysis.diagnostics import DiagnosticEngine
from onec_hbk_bsl.analysis.diagnostics_common_module import (
    common_module_has_api_region,
    common_module_xml_flags_invalid,
)


class _FakeIndex158:
    """Minimal stand-in for SymbolIndex metadata lookup."""

    def has_metadata(self) -> bool:
        return True

    def find_meta_object(self, name: str) -> dict[str, Any] | None:
        if name == "МойОбщийМодуль":
            return {"kind": "CommonModule", "name": "МойОбщийМодуль"}
        return None


def _write_module_xml(
    base: Path,
    *,
    server: str = "false",
    servercall: str = "false",
    coa: str = "false",
    cma: str = "false",
    ext: str = "false",
    gcm: str = "false",
) -> Path:
    bsl = base / "CommonModules" / "ТестМодуль" / "Ext" / "Module.bsl"
    bsl.parent.mkdir(parents=True)
    bsl.write_text("Процедура П() Экспорт\nКонецПроцедуры\n", encoding="utf-8")
    xml = base / "CommonModules" / "ТестМодуль" / "ТестМодуль.xml"
    xml.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" version="2.20">
  <CommonModule uuid="00000000-0000-0000-0000-000000000001">
    <Properties>
      <Name>ТестМодуль</Name>
      <Server>{server}</Server>
      <ServerCall>{servercall}</ServerCall>
      <ClientOrdinaryApplication>{coa}</ClientOrdinaryApplication>
      <ClientManagedApplication>{cma}</ClientManagedApplication>
      <ExternalConnection>{ext}</ExternalConnection>
      <GlobalClientManagedApplication>{gcm}</GlobalClientManagedApplication>
    </Properties>
  </CommonModule>
</MetaDataObject>
""",
        encoding="utf-8",
    )
    return bsl


def test_bsl158_assign_to_indexed_common_module(tmp_path: Path) -> None:
    p = tmp_path / "m.bsl"
    p.write_text("МойОбщийМодуль = 1;\n", encoding="utf-8")
    engine = DiagnosticEngine(select={"BSL158"}, symbol_index=_FakeIndex158())
    diags = [d for d in engine.check_file(str(p)) if d.code == "BSL158"]
    assert len(diags) == 1
    assert "МойОбщийМодуль" in diags[0].message


def test_bsl158_noop_without_metadata_index(tmp_path: Path) -> None:
    p = tmp_path / "m.bsl"
    p.write_text("МойОбщийМодуль = 1;\n", encoding="utf-8")
    engine = DiagnosticEngine(select={"BSL158"})
    assert not [d for d in engine.check_file(str(p)) if d.code == "BSL158"]


def test_bsl159_invalid_all_flags_false(tmp_path: Path) -> None:
    bsl = _write_module_xml(tmp_path)
    assert common_module_xml_flags_invalid(str(bsl)) is True
    engine = DiagnosticEngine(select={"BSL159"})
    diags = [d for d in engine.check_file(str(bsl)) if d.code == "BSL159"]
    assert len(diags) == 1


def test_bsl159_valid_server(tmp_path: Path) -> None:
    bsl = _write_module_xml(tmp_path, server="true")
    assert common_module_xml_flags_invalid(str(bsl)) is False
    engine = DiagnosticEngine(select={"BSL159"})
    assert not [d for d in engine.check_file(str(bsl)) if d.code == "BSL159"]


def test_bsl160_fires_without_api_region(tmp_path: Path) -> None:
    bsl = _write_module_xml(tmp_path, server="true")
    bsl.write_text(
        "#Область Прочее\n"
        "Процедура П() Экспорт\n"
        "КонецПроцедуры\n"
        "#КонецОбласти\n",
        encoding="utf-8",
    )
    engine = DiagnosticEngine(select={"BSL160"})
    diags = [d for d in engine.check_file(str(bsl)) if d.code == "BSL160"]
    assert len(diags) == 1


def test_bsl160_clean_with_public_and_export(tmp_path: Path) -> None:
    bsl = _write_module_xml(tmp_path, server="true")
    bsl.write_text(
        "#Область ПрограммныйИнтерфейс\n"
        "Процедура П() Экспорт\n"
        "КонецПроцедуры\n"
        "#КонецОбласти\n",
        encoding="utf-8",
    )
    engine = DiagnosticEngine(select={"BSL160"})
    assert not [d for d in engine.check_file(str(bsl)) if d.code == "BSL160"]


def test_common_module_has_api_region_names() -> None:
    assert common_module_has_api_region(["ПрограммныйИнтерфейс", "Левое"])
    assert common_module_has_api_region(["internal"])
    assert not common_module_has_api_region(["Служебные"])


@pytest.mark.parametrize(
    "body,expect",
    [
        ("Процедура П()\nКонецПроцедуры\n", True),
        (
            "#Область ПрограммныйИнтерфейс\nПроцедура П() Экспорт\nКонецПроцедуры\n#КонецОбласти\n",
            False,
        ),
    ],
)
def test_bsl160_no_export_triggers(
    tmp_path: Path, body: str, expect: bool
) -> None:
    bsl = _write_module_xml(tmp_path, server="true")
    bsl.write_text(body, encoding="utf-8")
    engine = DiagnosticEngine(select={"BSL160"})
    diags = [d for d in engine.check_file(str(bsl)) if d.code == "BSL160"]
    assert (len(diags) >= 1) == expect
