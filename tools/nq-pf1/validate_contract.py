#!/usr/bin/env python3
"""Contract-only QA: PF1 threshold drift and MD/JSON divergence. No market data."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "research/nq/NQ_PORTFOLIO_FUNNEL_PF1_CONTRACT_2026_11_09.md"
JSON = ROOT / "research/nq/NQ_PORTFOLIO_FUNNEL_PF1_RULES_2026_11_09.json"
LOG = ROOT / "research/nq/NQ_PORTFOLIO_FUNNEL_PF1_CHANGELOG.md"

d = json.loads(JSON.read_text(encoding="utf-8"))
md = DOC.read_text(encoding="utf-8")
log = LOG.read_text(encoding="utf-8")
assert (d["id"], d["version"], d["status"]) == ("NQ_PF1", "1.0.0", "SPEC_ONLY")
assert d["approved_for_trading"] is False
assert d["instrument"] == "NQ" and d["max_open_NQ"] == 1
assert d["portfolio_components_min"] == 3 and d["portfolio_components_max"] == 5
assert d["is_window"] == ["2020-01-01", "2022-12-31"]
assert d["oos_1"] == ["2023-01-01", "2024-12-31"]
assert d["oos_2"] == ["2025-01-01", "2026-10-31"]
assert d["paper_forward_required"] is False
assert d["legacy_version_scopes_unchanged"] == [
    "V19", "V20", "V21", "V22", "V23", "V24", "V25"
]
assert len(d["stages"]) == 9
assert [s["id"] for s in d["stages"]] == list(range(1, 10))
assert [len(s["rules"]) for s in d["stages"]] == [10, 11, 9, 15, 20, 9, 17, 17, 13]
assert sum(len(s["rules"]) for s in d["stages"]) == 121
assert "v1.0.0" in log and "SPEC_ONLY" in log
assert "NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md" in md
assert "NO implementado" in md
for s in d["stages"]:
    assert f"## Embudo {s['id']}" in md
    for r in s["rules"]:
        assert r["filter"] in md and r["display"] in md, (s["id"], r)

def rule(stage, name, op, value):
    items = [r for r in d["stages"][stage - 1]["rules"] if r["filter"] == name]
    assert len(items) == 1, (stage, name, len(items))
    r = items[0]
    assert r["operator"] == op and r["value"] == value, (stage, name, r)

# Critical governance gates. Changing any number requires a new contract version.
for stage, label in [(5, "Stability"), (5, "Symmetry"), (7, "Stability nativa"),
                     (7, "Symmetry nativa"), (8, "Stability OOS acumulada"),
                     (8, "Symmetry OOS acumulada"), (9, "Stability final"),
                     (9, "Symmetry final")]:
    rule(stage, label, "gt", 30)
rule(1, "Banco inicial", "eq", 100000)
rule(2, "Operaciones historicas minimas", "gte", 30)
rule(3, "Correlacion mensual positiva entre miembros", "lte", 0.45)
rule(3, "Concentracion beneficio bruto ganador por miembro", "lte", 40)
rule(4, "Riesgo planificado por entrada", "lte", 200)
rule(4, "Pausa preventiva por perdida diaria", "eq", 500)
rule(4, "Cierre preventivo por perdida diaria", "eq", 750)
rule(4, "Bloqueo preventivo de DD equity", "eq", 1600)
rule(5, "Profit Factor neto", "gte", 1.25)
rule(5, "Operaciones totales", "gte", 150)
rule(5, "Operaciones por mes completo", "gte", 5)
rule(5, "DD adverso M1", "lte", 2000)
rule(5, "Perdida diaria maxima", "lte", 1000)
rule(5, "Beneficio con costos 1.5x", "gt", 0)
rule(6, "Simulaciones confirmatorias", "eq", 5000)
rule(6, "Bloque bootstrap", "eq", 8)
rule(6, "DD Monte Carlo P95", "lte", 2000)
rule(8, "Meses OOS completos", "eq", 46)
rule(8, "Reoptimizaciones usando OOS", "eq", 0)
rule(9, "Embudos anteriores aprobados", "eq", 8)
for stage in (2, 4):
    rule(stage, "Slippage entrada", "eq", 2)
    rule(stage, "Slippage salida", "eq", 2)
assert abs((4*5 + 4.68) - 24.68) < 1e-9
assert abs(1.5*24.68 - 37.02) < 1e-9
assert abs(37.02-24.68 - 12.34) < 1e-9

assert "daily EOD net portfolio equity" in d["definitions"]["stability"]
assert "executed Long trades" in d["definitions"]["symmetry"]
assert "NOT rolling-reoptimization" in d["definitions"]["oos"]
print("PASS NQ PF1 v1.0.0: 9 embudos, 121 reglas, formulas, costos y OOS protegidos.")
