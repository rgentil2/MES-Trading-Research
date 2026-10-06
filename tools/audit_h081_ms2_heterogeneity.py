#!/usr/bin/env python3
"""H081 x MES-MS2 frozen pre-open state heterogeneity audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PRIMARY = "net_pnl_30"
STRESS = "stress_net_pnl_30"
MIN_GROUP_N = 15
PERMUTATIONS = 5000
BASE_SEED = 20261005

FAMILIES = [
    "volatility_state",
    "efficiency_state",
    "direction",
    "overnight_state",
    "volume_state",
    "gap_state",
    "value_location",
]


def profit_factor(pnl: pd.Series) -> float:
    wins = float(pnl[pnl > 0].sum())
    losses = float(-pnl[pnl < 0].sum())
    if losses == 0:
        return float("inf") if wins > 0 else float("nan")
    return wins / losses


def group_metrics(g: pd.DataFrame) -> dict:
    pnl = g[PRIMARY].astype(float)
    stress = g[STRESS].astype(float)
    return {
        "trades": int(len(g)),
        "net_pnl_usd": float(pnl.sum()),
        "expectancy_usd": float(pnl.mean()),
        "stress_expectancy_usd": float(stress.mean()),
        "profit_factor": float(profit_factor(pnl)),
        "win_rate": float((pnl > 0).mean()),
    }


def between_group_stat(values: np.ndarray, groups: np.ndarray) -> float:
    overall = float(values.mean())
    stat = 0.0
    for label in np.unique(groups):
        x = values[groups == label]
        stat += len(x) * (float(x.mean()) - overall) ** 2
    return float(stat)


def omnibus_test(d: pd.DataFrame, family: str, family_index: int) -> dict:
    x = d[(d["input_status"] == "READY") & (d[family] != "UNKNOWN")].copy()
    counts = x[family].value_counts()
    keep = counts[counts >= MIN_GROUP_N].index.tolist()
    x = x[x[family].isin(keep)].copy()

    if len(keep) < 2:
        return {
            "family": family,
            "eligible_trades": int(len(x)),
            "eligible_categories": "|".join(map(str, keep)),
            "categories_tested": int(len(keep)),
            "observed_stat": None,
            "p_value": 1.0,
            "testable": False,
        }

    values = x[PRIMARY].to_numpy(float)
    groups = x[family].astype(str).to_numpy()
    observed = between_group_stat(values, groups)

    rng = np.random.default_rng(BASE_SEED + family_index)
    exceed = 0
    for _ in range(PERMUTATIONS):
        perm = rng.permutation(values)
        if between_group_stat(perm, groups) >= observed - 1e-12:
            exceed += 1
    p = (1 + exceed) / (PERMUTATIONS + 1)

    return {
        "family": family,
        "eligible_trades": int(len(x)),
        "eligible_categories": "|".join(map(str, keep)),
        "categories_tested": int(len(keep)),
        "observed_stat": observed,
        "p_value": float(p),
        "testable": True,
    }


def bh_adjust(pvalues: list[float]) -> list[float]:
    p = np.asarray(pvalues, float)
    order = np.argsort(p)
    ranked = p[order]
    q = np.empty_like(ranked)
    running = 1.0
    m = len(p)
    for i in range(m - 1, -1, -1):
        rank = i + 1
        running = min(running, ranked[i] * m / rank)
        q[i] = running
    out = np.empty_like(q)
    out[order] = np.minimum(q, 1.0)
    return out.tolist()


def pf_text(x) -> str:
    if x is None or pd.isna(x):
        return "NA"
    if np.isinf(x):
        return "∞"
    return f"{x:.3f}"


def markdown(report: dict, tests: pd.DataFrame, groups: pd.DataFrame,
             regimes: pd.DataFrame) -> str:
    lines = [
        "# H081 x MES-MS2 — heterogeneidad por estado pre-open",
        "",
        "Diagnóstico post-hoc con H081 congelado y features MES-MS2 causales a 09:30 ET. "
        "No se cambió la estrategia y 2026 no fue abierto.",
        "",
        "## Cobertura",
        "",
        f"- H081 trades 2020-2024: **{report['h081_scope_trades']}**.",
        f"- Trades unidos a MES-MS2: **{report['joined_trades']}**.",
        f"- Con input_status READY: **{report['ready_trades']}**.",
        "",
        "## Tests omnibus",
        "",
        "| Familia | N elegible | Categorías | p | BH q | Heterogeneidad q<0.05 |",
        "|---|---:|---|---:|---:|---|",
    ]
    for r in tests.itertuples(index=False):
        lines.append(
            f"| {r.family} | {r.eligible_trades} | {r.eligible_categories or 'NA'} | "
            f"{r.p_value:.4f} | {r.q_value_bh:.4f} | "
            f"{'SÍ' if r.q_value_bh < 0.05 else 'NO'} |"
        )

    sig = tests[tests.q_value_bh < 0.05]
    lines += ["", "## Resultado principal", ""]
    if sig.empty:
        lines.append(
            "- **Ninguna** de las siete familias mostró heterogeneidad significativa "
            "después de FDR."
        )
    else:
        lines.append(
            "- Familias con heterogeneidad significativa: **"
            + ", ".join(sig.family.tolist())
            + "**."
        )

    lines += [
        "",
        "## Desglose completo por categoría",
        "",
        "| Familia | Categoría | N | Exp. neta | Exp. 1.5x | PF | Win rate |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in groups.itertuples(index=False):
        lines.append(
            f"| {r.family} | {r.category} | {r.trades} | "
            f"USD {r.expectancy_usd:.2f} | USD {r.stress_expectancy_usd:.2f} | "
            f"{pf_text(r.profit_factor)} | {100*r.win_rate:.1f}% |"
        )

    lines += [
        "",
        "## MES-MS2 R0-R4 en las fechas de H081",
        "",
        "| Estado | N | Exp. neta | PF |",
        "|---|---:|---:|---:|",
    ]
    for r in regimes.itertuples(index=False):
        lines.append(
            f"| {r.regime} | {r.trades} | USD {r.expectancy_usd:.2f} | "
            f"{pf_text(r.profit_factor)} |"
        )

    lines += [
        "",
        "Los R0-R4 se muestran sólo de forma descriptiva; no fueron parte de los "
        "siete tests porque la cobertura clasificada de MES-MS2 es limitada.",
        "",
        f"Filas 2026 abiertas: **{report['calendar_2026_rows_opened']}**.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--h081-dir", type=Path, required=True)
    p.add_argument("--ms2-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=Path("results/temporal/H081_MS2"))
    args = p.parse_args()

    hfiles = list(args.h081_dir.rglob("H081_trades.parquet"))
    mfiles = list(args.ms2_dir.rglob("MES_MS2_CAUSAL_FEATURES.csv"))
    if len(hfiles) != 1 or len(mfiles) != 1:
        raise ValueError(
            f"expected one H081 parquet and one MS2 feature CSV, got {len(hfiles)}, {len(mfiles)}"
        )

    h = pd.read_parquet(hfiles[0]).copy()
    h["session_date"] = pd.to_datetime(h["session_date"]).dt.strftime("%Y-%m-%d")
    h["year"] = pd.to_datetime(h["session_date"]).dt.year
    if (h.year >= 2026).any():
        raise ValueError("2026 present in archived H081 artifact")
    h = h[h.year.between(2020, 2024)].copy()

    m = pd.read_csv(mfiles[0], dtype={"date": str}).copy()
    if (pd.to_datetime(m["date"]).dt.year >= 2025).any():
        raise ValueError("MES-MS2 artifact escaped 2020-2024 scope")
    if m["date"].duplicated().any():
        raise ValueError("MES-MS2 dates are not unique")

    keep = ["date", "input_status", "regime"] + FAMILIES
    missing = set(keep) - set(m.columns)
    if missing:
        raise ValueError(f"missing MES-MS2 columns: {sorted(missing)}")

    j = h.merge(
        m[keep],
        left_on="session_date",
        right_on="date",
        how="left",
        validate="one_to_one",
    )
    if j["date"].isna().any():
        missing_dates = j.loc[j["date"].isna(), "session_date"].tolist()
        raise ValueError(f"H081 dates missing in MES-MS2: {missing_dates[:10]}")

    group_rows = []
    for family in FAMILIES:
        for category, g in j.groupby(family, sort=True, observed=True, dropna=False):
            label = "MISSING" if pd.isna(category) else str(category)
            group_rows.append(
                {"family": family, "category": label, **group_metrics(g)}
            )
    group_df = pd.DataFrame(group_rows)

    tests = pd.DataFrame(
        [omnibus_test(j, family, i) for i, family in enumerate(FAMILIES)]
    )
    tests["q_value_bh"] = bh_adjust(tests["p_value"].tolist())
    tests["significant_fdr_05"] = tests["q_value_bh"] < 0.05

    regime_rows = []
    for regime, g in j.groupby("regime", sort=True, observed=True, dropna=False):
        label = "MISSING" if pd.isna(regime) else str(regime)
        regime_rows.append({"regime": label, **group_metrics(g)})
    regimes = pd.DataFrame(regime_rows)

    report = {
        "authority": "POST_HOC_HETEROGENEITY_DIAGNOSTIC_ONLY",
        "h081_scope_trades": int(len(h)),
        "joined_trades": int(len(j)),
        "ready_trades": int((j.input_status == "READY").sum()),
        "families_tested": FAMILIES,
        "permutations_per_family": PERMUTATIONS,
        "minimum_group_n": MIN_GROUP_N,
        "significant_families_fdr_05": tests.loc[
            tests.significant_fdr_05, "family"
        ].tolist(),
        "calendar_2026_rows_opened": 0,
        "strategy_modified": False,
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    group_df.to_csv(out / "category_breakdown.csv", index=False)
    tests.to_csv(out / "omnibus_tests.csv", index=False)
    regimes.to_csv(out / "regime_breakdown.csv", index=False)
    (out / "H081_MS2_HETEROGENEITY_REPORT.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    md = markdown(report, tests, group_df, regimes)
    (out / "H081_MS2_HETEROGENEITY_REPORT.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
