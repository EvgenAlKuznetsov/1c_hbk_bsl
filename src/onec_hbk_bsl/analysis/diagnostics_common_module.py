"""
Common-module diagnostics aligned with BSLLS (BSL158–BSL160 and helpers).

BSL158 — assignment to a name that is a *common module* metadata object (needs index).
BSL159 — common module XML matches no BSLLS execution context (see ``flagsCheck`` in
``AbstractCommonModuleNameDiagnostic`` — same as raw-flag combinations, not «any tag true»).
BSL160 — common module has methods but no export and/or no Public/Internal API region.
"""

from __future__ import annotations

import re
from typing import Any

from onec_hbk_bsl.analysis.diagnostics_bsl152 import common_module_xml_for_module_bsl

_RE_SIMPLE_LHS_ASSIGN = re.compile(r"^\s*(\w+)\s*=(?!=)")
# BSLLS CommonModuleMissingAPIDiagnostic — Public / Internal API regions
_API_REGION_NAMES_CF = frozenset(
    {
        "public",
        "программныйинтерфейс",
        "internal",
        "служебныйпрограммныйинтерфейс",
    }
)


def _xml_bool_tag(text: str, local: str) -> bool:
    m = re.search(rf"<{local}>\s*(true|false)\s*</{local}>", text, re.IGNORECASE)
    return m is not None and m.group(1).lower() == "true"


def _bslls_common_module_invalid_type_flags(
    *,
    server_call: bool,
    server: bool,
    external_connection: bool,
    client_ordinary_application: bool,
    client_managed_application: bool,
    ordinary_app_support: bool = True,
) -> bool:
    """
    Mirrors BSLLS ``CommonModuleInvalidTypeDiagnostic.flagsCheck`` /
    ``AbstractCommonModuleNameDiagnostic`` (same boolean formulas on metadata flags).

    Returns ``True`` when the module matches *no* valid context (diagnostic should fire).
    """
    oa = client_ordinary_application or not ordinary_app_support

    def _is_client_application() -> bool:
        return oa and client_managed_application

    def _is_client_server() -> bool:
        return (
            not server_call
            and server
            and external_connection
            and _is_client_application()
        )

    def _is_client() -> bool:
        return (
            not server_call
            and not server
            and not external_connection
            and _is_client_application()
        )

    def _is_server_call() -> bool:
        return (
            server_call
            and server
            and not external_connection
            and not client_ordinary_application
            and not client_managed_application
        )

    def _is_server() -> bool:
        return (
            not server_call
            and server
            and external_connection
            and oa
            and not client_managed_application
        )

    ok = _is_server() or _is_server_call() or _is_client() or _is_client_server()
    return not ok


def common_module_xml_flags_invalid(module_bsl_path: str) -> bool | None:
    """
    BSL159 — BSLLS ``CommonModuleInvalidType``: metadata does not describe any allowed
    execution context (server / server call / client / client-server).

    Uses the same four predicates as BSLLS on sibling ``<Name>.xml`` booleans
    (``Server``, ``ServerCall``, ``ExternalConnection``, ``ClientOrdinaryApplication``,
    ``ClientManagedApplication``). If the XML does not contain the known property tags,
    returns ``None`` (unknown / legacy layout).
    """
    xp = common_module_xml_for_module_bsl(module_bsl_path)
    if xp is None:
        return None
    try:
        raw = xp.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    if "<commonmodule" not in raw.casefold():
        return None
    if not re.search(
        r"<(?:Server|ServerCall|ClientOrdinaryApplication|ClientManagedApplication|"
        r"ExternalConnection|GlobalClientManagedApplication)\s*>",
        raw,
        re.IGNORECASE,
    ):
        return None
    s = _xml_bool_tag(raw, "Server")
    sc = _xml_bool_tag(raw, "ServerCall")
    coa = _xml_bool_tag(raw, "ClientOrdinaryApplication")
    cma = _xml_bool_tag(raw, "ClientManagedApplication")
    ext = _xml_bool_tag(raw, "ExternalConnection")
    return _bslls_common_module_invalid_type_flags(
        server_call=sc,
        server=s,
        external_connection=ext,
        client_ordinary_application=coa,
        client_managed_application=cma,
    )


def bsl158_common_module_assign_spans(
    lines: list[str],
    symbol_index: Any,
) -> list[tuple[int, int, int, str]]:
    """
    Return (line_1based, c0, c1, module_name) for simple ``Name =`` assignments
    where *Name* is indexed as ``CommonModule``.
    """
    if symbol_index is None or not getattr(symbol_index, "has_metadata", lambda: False)():
        return []
    out: list[tuple[int, int, int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        m = _RE_SIMPLE_LHS_ASSIGN.match(line)
        if not m:
            continue
        name = m.group(1)
        mo = symbol_index.find_meta_object(name)
        if mo is None or mo.get("kind") != "CommonModule":
            continue
        c0, c1 = m.start(1), m.end(1)
        out.append((i + 1, c0, c1, name))
    return out


def common_module_has_api_region(region_names: list[str]) -> bool:
    for n in region_names:
        if n.strip().casefold() in _API_REGION_NAMES_CF:
            return True
    return False


def bsl160_common_module_missing_api(
    module_bsl_path: str,
    region_names: list[str],
    procedures_export: list[bool],
) -> bool:
    """
    True if diagnostic should be raised (BSLLS ``CommonModuleMissingAPIDiagnostic``).

    *procedures_export*: ``is_export`` for each procedure/function in module order.
    """
    if common_module_xml_for_module_bsl(module_bsl_path) is None:
        return False
    if not procedures_export:
        return False
    no_export = not any(procedures_export)
    no_api_region = not common_module_has_api_region(region_names)
    return no_export or no_api_region


def bsl160_module_line1_span(lines: list[str]) -> tuple[int, int] | None:
    """Range on first line for whole-module diagnostic."""
    if not lines:
        return None
    line = lines[0]
    c0 = len(line) - len(line.lstrip())
    c1 = len(line.rstrip())
    if c1 <= c0:
        return 0, 1
    return c0, c1
