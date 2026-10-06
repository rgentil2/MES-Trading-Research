#!/usr/bin/env python3
"""Frozen post-hoc temporal robustness audit for MES H081/R072."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PRIMARY = "net_pnl_30"
STRESS = "stress_net_pnl_30"
EXPECTED_TRADES = 184
SOURCE_RUN_ID = 36427711138
SOURCE_ARTIFACT = "b14-opposite-sign-candidates"


def profit_factor(pnl: pd.Series) -> float:
    wins = float(pnl[pnl > 0].sum())
    losses = float(-pnl[pnl < 0].sum())
    if losses == 0:
        return float("inf") if wins > 0 else float("nan")
    return wins / losses


def metrics(g: pd.DataFrame) -> dict:
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


def grouped_metrics(d: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    for label, g in d.groupby(key, sort=True, observed=True):
        rows.append({key: str(label), **metrics(g)})
    return pd.DataFrame(rows)


def rolling_summary(d: pd.DataFrame, window: int) -> tuple[pd.DataFrame, dict]:
    roll = d[PRIMARY].rolling(window).mean()
    out = pd.DataFrame(
        {
            "window_end_trade": np.arange(1, len(d) + 1, dtype=int),
            "window": window,
            "rolling_expectancy_usd": roll,
        }
    ).dropna()
    return out, {
        "window": window,
        "windows": int(len(out)),
        "positive_share": float((out.rolling_expectancy_usd > 0).mean()),
        "median_expectancy_usd": float(out.rolling_expectancy_usd.median()),
        "min_expectancy_usd": float(out.rolling_expectancy_usd.min()),
        "max_expectancy_usd": float(out.rolling_expectancy_usd.max()),
    }


def leave_one_year_out(d: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"omitted_year": int(year), **metrics(d[d.year != year])}
            for year in sorted(d.year.unique())
        ]
    )


def markdown(report: dict, yearly: pd.DataFrame, half: pd.DataFrame,
             loo: pd.DataFrame) -> str:
    a = report["aggregate"]
    c = report["concentration"]
    r20 = report["rolling"]["20"]
    r40 = report["rolling"]["40"]
    lines = [
        "# H081 / R072 — auditoría de robustez temporal",
        "",
        "Diagnóstico post-hoc congelado antes de abrir el artefacto de trades. "
        "No se modificó la señal ni se abrió 2026.",
        "",
        "## Resultado agregado reproducido",
        "",
        f"- Trades: **{a['trades']}**.",
        f"- Expectativa neta 30m: **USD {a['expectancy_usd']:.2f}/trade**.",
        f"- P&L neto: **USD {a['net_pnl_usd']:.2f}**.",
        f"- PF: **{a['profit_factor']:.3f}**.",
        f"- Expectativa con 1.5x costes: **USD {a['stress_expectancy_usd']:.2f}/trade**.",
        "",
        "## Por año",
        "",
        "| Año | Trades | Exp. neta | P&L neto | PF |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in yearly.itertuples(index=False):
        lines.append(
            f"| {row.year} | {row.trades} | USD {row.expectancy_usd:.2f} | "
            f"USD {row.net_pnl_usd:.2f} | {row.profit_factor:.3f} |"
        )
    lines += [
        "",
        "## Por semestre",
        "",
        "| Semestre | Trades | Exp. neta | P&L neto | PF |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in half.itertuples(index=False):
        lines.append(
            f"| {row.half_year} | {row.trades} | USD {row.expectancy_usd:.2f} | "
            f"USD {row.net_pnl_usd:.2f} | {row.profit_factor:.3f} |"
        )
    lines += [
        "",
        "## Concentración",
        "",
        f"- Mejor trimestre: **{c['best_quarter']}**, aporta "
        f"**{100*c['best_quarter_share_total_net']:.1f}%** del P&L neto agregado.",
        f"- Cinco mejores trades: aportan "
        f"**{100*c['top5_winners_share_total_net']:.1f}%** del P&L neto agregado.",
        f"- Quitando el mejor trimestre: expectativa **USD {c['drop_best_quarter_expectancy_usd']:.2f}/trade**.",
        f"- Quitando los cinco mejores trades: expectativa **USD {c['drop_top5_expectancy_usd']:.2f}/trade**.",
        "",
        "## Ventanas móviles",
        "",
        f"- 20 trades: {100*r20['positive_share']:.1f}% positivas; "
        f"mediana USD {r20['median_expectancy_usd']:.2f}, "
        f"mínimo USD {r20['min_expectancy_usd']:.2f}, máximo USD {r20['max_expectancy_usd']:.2f}.",
        f"- 40 trades: {100*r40['positive_share']:.1f}% positivas; "
        f"mediana USD {r40['median_expectancy_usd']:.2f}, "
        f"mínimo USD {r40['min_expectancy_usd']:.2f}, máximo USD {r40['max_expectancy_usd']:.2f}.",
        "",
        "## Leave-one-year-out",
        "",
        "| Año eliminado | Trades | Exp. neta | PF |",
        "|---|---:|---:|---:|",
    ]
    for row in loo.itertuples(index=False):
        lines.append(
            f"| {row.omitted_year} | {row.trades} | USD {row.expectancy_usd:.2f} | "
            f"{row.profit_factor:.3f} |"
        )
    lines += ["", "## Flags preregistrados", ""]
    if report["flags"]:
        lines.extend([f"- **FLAG:** {flag}" for flag in report["flags"]])
    else:
        lines.append("- Ningún flag de concentración temporal se activó.")
    lines += [
        "",
        f"Flags activados: **{len(report['flags'])}/7**.",
        "",
        "Las tablas mensuales, trimestrales y semanales completas se guardan como CSV. "
        "No se selecciona ningún mes o semana ganador como nueva regla.",
        "",
        "MES 2026 permaneció completamente cerrado.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=Path("results/temporal/H081"))
    args = p.parse_args()

    matches = list(args.input_dir.rglob("H081_trades.parquet"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one H081_trades.parquet, found {len(matches)}")
    source = matches[0]
    d = pd.read_parquet(source).copy()

    required = {"session_date", "year", "entry_clock_et", PRIMARY, STRESS}
    if not required <= set(d.columns):
        raise ValueError(f"missing H081 fields: {sorted(required-set(d.columns))}")
    if len(d) != EXPECTED_TRADES:
        raise ValueError(f"archived H081 trade count drift: {len(d)} != {EXPECTED_TRADES}")

    d["entry_clock_et"] = pd.to_datetime(d["entry_clock_et"], utc=True).dt.tz_convert(
        "America/New_York"
    )
    d["date"] = pd.to_datetime(d["session_date"])
    d["year"] = d["date"].dt.year.astype(int)
    if d.year.min() < 2020 or d.year.max() > 2025 or (d.year >= 2026).any():
        raise ValueError("source artifact escaped frozen 2020-2025 scope")

    d = d.sort_values("entry_clock_et").reset_index(drop=True)
    d["quarter"] = d["date"].dt.to_period("Q").astype(str)
    d["month"] = d["date"].dt.to_period("M").astype(str)
    d["half_year"] = d["year"].astype(str) + np.where(
        d["date"].dt.month <= 6, "-H1", "-H2"
    )
    iso = d["date"].dt.isocalendar()
    d["iso_week"] = (
        iso.year.astype(str) + "-W" + iso.week.astype(str).str.zfill(2)
    )

    aggregate = metrics(d)
    yearly = grouped_metrics(d, "year")
    quarterly = grouped_metrics(d, "quarter")
    monthly = grouped_metrics(d, "month")
    half = grouped_metrics(d, "half_year")
    weekly = grouped_metrics(d, "iso_week")
    roll20, roll20_summary = rolling_summary(d, 20)
    roll40, roll40_summary = rolling_summary(d, 40)
    loo = leave_one_year_out(d)

    total_net = aggregate["net_pnl_usd"]
    if total_net <= 0:
        raise ValueError("H081 aggregate no longer matches positive archived result")

    best_q_row = quarterly.loc[quarterly.net_pnl_usd.idxmax()]
    best_quarter = str(best_q_row["quarter"])
    best_quarter_share = float(best_q_row["net_pnl_usd"] / total_net)

    top5_idx = d.nlargest(5, PRIMARY).index
    top5_sum = float(d.loc[top5_idx, PRIMARY].sum())
    top5_share = float(top5_sum / total_net)
    drop_best_q = d[d.quarter != best_quarter]
    drop_top5 = d.drop(index=top5_idx)

    positive_half_share = float((half.expectancy_usd > 0).mean())
    loo_min_expectancy = float(loo.expectancy_usd.min())

    concentration = {
        "best_quarter": best_quarter,
        "best_quarter_net_pnl_usd": float(best_q_row["net_pnl_usd"]),
        "best_quarter_share_total_net": best_quarter_share,
        "top5_winners_net_pnl_usd": top5_sum,
        "top5_winners_share_total_net": top5_share,
        "drop_best_quarter_expectancy_usd": float(drop_best_q[PRIMARY].mean()),
        "drop_top5_expectancy_usd": float(drop_top5[PRIMARY].mean()),
        "positive_half_year_share": positive_half_share,
        "leave_one_year_out_min_expectancy_usd": loo_min_expectancy,
    }

    flags = []
    if best_quarter_share > 0.50:
        flags.append("BEST_QUARTER_GT_50PCT_TOTAL_NET")
    if top5_share > 0.50:
        flags.append("TOP5_WINNERS_GT_50PCT_TOTAL_NET")
    if concentration["drop_best_quarter_expectancy_usd"] <= 0:
        flags.append("DROP_BEST_QUARTER_EXPECTANCY_NONPOSITIVE")
    if concentration["drop_top5_expectancy_usd"] <= 0:
        flags.append("DROP_TOP5_EXPECTANCY_NONPOSITIVE")
    if positive_half_share < 0.50:
        flags.append("LESS_THAN_HALF_HALFYEARS_POSITIVE")
    if roll20_summary["positive_share"] < 0.50:
        flags.append("LESS_THAN_HALF_ROLLING20_POSITIVE")
    if loo_min_expectancy <= 0:
        flags.append("SOME_LEAVE_ONE_YEAR_OUT_EXPECTANCY_NONPOSITIVE")

    report = {
        "authority": "POST_HOC_TEMPORAL_DIAGNOSTIC_ONLY",
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact": SOURCE_ARTIFACT,
        "source_file": source.name,
        "strategy_modified": False,
        "calendar_2026_opened": False,
        "aggregate": aggregate,
        "rolling": {"20": roll20_summary, "40": roll40_summary},
        "concentration": concentration,
        "flags": flags,
        "positive_year_share": float((yearly.expectancy_usd > 0).mean()),
        "positive_quarter_share": float((quarterly.expectancy_usd > 0).mean()),
        "positive_month_share": float((monthly.expectancy_usd > 0).mean()),
        "positive_half_year_share": positive_half_share,
        "nonempty_weeks": int(len(weekly)),
        "positive_week_share": float((weekly.expectancy_usd > 0).mean()),
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    yearly.to_csv(out / "yearly.csv", index=False)
    quarterly.to_csv(out / "quarterly.csv", index=False)
    monthly.to_csv(out / "monthly.csv", index=False)
    half.to_csv(out / "half_year.csv", index=False)
    weekly.to_csv(out / "weekly.csv", index=False)
    roll20.to_csv(out / "rolling20.csv", index=False)
    roll40.to_csv(out / "rolling40.csv", index=False)
    loo.to_csv(out / "leave_one_year_out.csv", index=False)
    (out / "H081_TEMPORAL_REPORT.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    md = markdown(report, yearly, half, loo)
    (out / "H081_TEMPORAL_REPORT.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
