#!/usr/bin/env python3
"""Post-selection engineering ONLY for 4 existing, nonconfirmed NQ signals, DEV 2020-24.
No 2025/2026 input file opened; no strategy is validated by this computation.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from research.nq.nq_h05_h07_level_volume_screen import load_development, roll_contract
except ModuleNotFoundError:
    from nq_h05_h07_level_volume_screen import load_development, roll_contract

PRIORITY = {'NQ-H09': 0, 'NQ-H02': 1, 'NQ-H01': 2, 'NQ-H05': 3}
HYPOTHESES = list(PRIORITY)
STOPS = (0.10, 0.15, 0.20)
TARGETS = (1.0, 1.5, 2.0)
TIMEOUTS = (30, 60)
FEES = {'NQ': 5.74, 'MNQ': 1.88}
MULTIPLIERS = {'NQ': 20.0, 'MNQ': 2.0}
TICK = 0.25
ENTRY_SLIP_POINTS = EXIT_SLIP_POINTS = 2 * TICK
START_MINUTES = 9 * 60 + 31
SEED = 20261009
BOOT = 3000


def standardize(csv_h01: Path, csv_h05: Path, csv_h09: Path) -> pd.DataFrame:
    sources = (
        (csv_h01, ('NQ-H01', 'NQ-H02'), 'session', 'signal_time_et'),
        (csv_h05, ('NQ-H05',), 'session', 'signal_time_et'),
        (csv_h09, ('NQ-H09',), 'day', 'signal_et'),
    )
    frames = []
    for path, hs, dcol, tcol in sources:
        frame = pd.read_csv(path)
        required = {'hypothesis', dcol, tcol, 'side', 'entry_open'}
        if not required.issubset(frame):
            raise ValueError(f'Event artifact is missing required fields: {path}')
        frame = frame[frame.hypothesis.isin(hs)].copy()
        frame = frame.rename(columns={dcol: 'session', tcol: 'signal_time_et'})
        frame['source_file'] = path.name
        frames.append(frame[['session', 'hypothesis', 'signal_time_et', 'side', 'entry_open', 'source_file']])
    joined = pd.concat(frames, ignore_index=True)
    if joined.duplicated(['session', 'hypothesis']).any():
        raise ValueError('Multiple existing signals for the same hypothesis/session')
    if not joined.hypothesis.isin(PRIORITY).all():
        raise ValueError('Unexpected hypothesis')
    if not joined.side.isin(['LONG', 'SHORT']).all():
        raise ValueError('Unexpected position side')
    return joined


def prepare_events(events: pd.DataFrame, dates: list[str], arr: np.ndarray):
    date_to_idx = {d: i for i, d in enumerate(dates)}
    complete = []
    reasons = {}
    def exclude(reason):
        reasons[reason] = reasons.get(reason, 0) + 1
    for e in events.itertuples(index=False):
        d = str(e.session)
        if not (d[:4] in ('2020', '2021', '2022', '2023', '2024')):
            raise ValueError('Hard isolation failure: non-DEV signal year')
        t = date_to_idx.get(d)
        if t is None:
            exclude('no_complete_RTH_day'); continue
        if t < 14:
            exclude('prior14_RTH_unavailable'); continue
        if e.hypothesis == 'NQ-H05':
            prev_d = date.fromisoformat(dates[t - 1])
            curr_d = date.fromisoformat(d)
            if roll_contract(curr_d) != roll_contract(prev_d):
                exclude('H05_cross_contract_prior_day'); continue
            if (curr_d - prev_d).days > 5:
                exclude('H05_stale_prior_day'); continue
        hh, mm = map(int, str(e.signal_time_et).split(':'))
        signal_idx = hh * 60 + mm - START_MINUTES
        entry_idx = signal_idx + 1
        if not 0 <= signal_idx < 90 or entry_idx + max(TIMEOUTS) >= 390:
            exclude('invalid_clock_or_time_horizon'); continue
        actual_entry = float(arr[t, entry_idx, 0])
        if not np.isclose(actual_entry, float(e.entry_open), atol=0.000001, rtol=0):
            exclude('original_signal_entry_source_mismatch'); continue
        hist = arr[t - 14:t]
        historical_ranges = hist[:, :, 1].max(axis=1) - hist[:, :, 2].min(axis=1)
        med = float(np.median(historical_ranges))
        if not med > 0 or not np.isfinite(med):
            exclude('invalid_past_range'); continue
        complete.append({
            'session': d, 'year': int(d[:4]), 'hypothesis': e.hypothesis,
            'signal_time_et': e.signal_time_et, 'side': e.side,
            'date_ix': t, 'signal_ix': signal_idx, 'entry_ix': entry_idx,
            'median_prior14_rth_range_pts': med, 'entry_open': actual_entry,
            'source_file': e.source_file,
            'week': str(pd.Timestamp(d).to_period('W-SUN')),
            'priority': PRIORITY[e.hypothesis],
        })
    output = pd.DataFrame.from_records(complete)
    if output.empty:
        raise ValueError('No source-matched eligible pre-existing signal')
    output = output.sort_values(['session', 'entry_ix', 'priority', 'hypothesis'], kind='stable').reset_index(drop=True)
    return output, reasons


def simulate_bar_path(bars: np.ndarray, entry_idx: int, side: int, width: float, rr: float,
                      timeout: int, fee: float, multiplier: float) -> dict:
    """First bar is entered at open; time exit at open of entry_idx+timeout.
    All ambiguous SL+TP minutes are STOP-first. Every exit receives adverse 2 ticks.
    """
    entry_open = float(bars[entry_idx, 0])
    entry_fill = entry_open + side * ENTRY_SLIP_POINTS
    stop = entry_fill - side * width
    target = entry_fill + side * rr * width
    ambig = False
    reason = 'TIME'
    raw_exit = float(bars[entry_idx + timeout, 0])
    holding = timeout
    gap_exit = False
    for offset in range(timeout):
        ix = entry_idx + offset
        op, hi, lo = map(float, bars[ix, :3])
        if side > 0:
            stop_open = op <= stop
            target_open = op >= target
            hit_stop = lo <= stop
            hit_target = hi >= target
        else:
            stop_open = op >= stop
            target_open = op <= target
            hit_stop = hi >= stop
            hit_target = lo <= target
        if stop_open:
            raw_exit, reason, holding, gap_exit = op, 'STOP', offset, True
            break
        if target_open:
            raw_exit, reason, holding = target, 'TARGET', offset
            break
        if hit_stop and hit_target:
            ambig = True
        if hit_stop:
            raw_exit, reason, holding = stop, 'STOP', offset + 1
            break
        if hit_target:
            raw_exit, reason, holding = target, 'TARGET', offset + 1
            break
    exit_fill = raw_exit - side * EXIT_SLIP_POINTS
    pnl = side * (exit_fill - entry_fill) * multiplier - fee
    return {
        'pnl': float(pnl), 'exit_reason': reason, 'ambiguous_bar_stop_first': ambig,
        'stop_gap_through': gap_exit, 'exit_bar_offset': holding,
        'entry_fill': entry_fill, 'exit_fill': exit_fill,
        'stop_level': stop, 'target_level': target,
    }


def compute_trades(events: pd.DataFrame, arr: np.ndarray) -> pd.DataFrame:
    lines = []
    for e in events.itertuples(index=False):
        a = arr[e.date_ix]
        side = 1 if e.side == 'LONG' else -1
        for stop_frac in STOPS:
            width = max(1.0, stop_frac * e.median_prior14_rth_range_pts)
            for target_r in TARGETS:
                for timeout in TIMEOUTS:
                    for instrument in ('NQ', 'MNQ'):
                        result = simulate_bar_path(a, e.entry_ix, side, width, target_r, timeout,
                            FEES[instrument], MULTIPLIERS[instrument])
                        friction = FEES[instrument] + (ENTRY_SLIP_POINTS + EXIT_SLIP_POINTS) * MULTIPLIERS[instrument]
                        lines.append({
                            'session': e.session, 'year': e.year, 'week': e.week,
                            'hypothesis': e.hypothesis, 'signal_time_et': e.signal_time_et,
                            'side': e.side, 'entry_open': e.entry_open,
                            'instrument_accounting': instrument,
                            'stop_frac': stop_frac, 'target_r': target_r,
                            'timeout_min': timeout,
                            'stop_width_pts': width,
                            'nominal_full_stop_usd': width * MULTIPLIERS[instrument]
                                + EXIT_SLIP_POINTS * MULTIPLIERS[instrument] + FEES[instrument],
                            'pnl_usd': result['pnl'],
                            'pnl_cost_stress_1_5x_usd': result['pnl'] - 0.5 * friction,
                            'exit_reason': result['exit_reason'],
                            'same_bar_stop_target_ambiguity': result['ambiguous_bar_stop_first'],
                            'stop_gap_through': result['stop_gap_through'],
                            'entry_fill': result['entry_fill'], 'exit_fill': result['exit_fill'],
                            'max_holding_bars': result['exit_bar_offset'],
                        })
    return pd.DataFrame(lines)


def week_boot_ci90(g: pd.DataFrame, seed_offset: int) -> list[float]:
    rng = np.random.default_rng(SEED + seed_offset)
    w = g.groupby('week').pnl_usd.agg(['sum', 'count']).to_numpy(float)
    estimates = []
    for _ in range(0, BOOT, 200):
        n = min(200, BOOT - len(estimates))
        inds = rng.integers(0, len(w), size=(n, len(w)))
        s = w[inds]
        estimates.extend((s[:, :, 0].sum(axis=1)/s[:, :, 1].sum(axis=1)).tolist())
    return [round(float(x), 2) for x in np.quantile(estimates, [0.05, 0.95])]


def calc_summary(trades: pd.DataFrame, hypothesis_col: bool = True) -> pd.DataFrame:
    keys = ['instrument_accounting', 'stop_frac', 'target_r', 'timeout_min']
    if hypothesis_col:
        keys = ['hypothesis'] + keys
    rows = []
    for idx, (key, g) in enumerate(trades.groupby(keys, sort=True)):
        if not isinstance(key, tuple): key=(key,)
        x = g.pnl_usd.to_numpy(float)
        eq = np.cumsum(x)
        dd = np.maximum.accumulate(np.r_[0., eq])[1:] - eq
        pos = x[x>0].sum()
        neg = -x[x<0].sum()
        means = g.groupby('year').pnl_usd.mean().to_dict()
        days = pd.to_datetime(g.session.drop_duplicates().sort_values())
        gaps = days.diff().dt.days.dropna()
        row = dict(zip(keys, key))
        row.update({
            'trades': len(g), 'mean_net_usd': round(float(x.mean()), 2),
            'total_net_usd': round(float(x.sum()), 2),
            'profit_factor': round(float(pos/neg), 3) if neg>0 else None,
            'win_rate': round(float((x>0).mean()), 4),
            'closed_trade_max_dd_usd': round(float(dd.max()), 2),
            'positive_years': sum(y in means and means[y]>0 for y in range(2020,2025)),
            'annual_means_usd': {str(y): round(float(means[y]),2) if y in means else None
                                 for y in range(2020,2025)},
            'ci90_week_boot_usd': week_boot_ci90(g, idx),
            'stressed_mean_net_usd': round(float(g.pnl_cost_stress_1_5x_usd.mean()),2),
            'stop_rate': round(float((g.exit_reason=='STOP').mean()),4),
            'target_rate': round(float((g.exit_reason=='TARGET').mean()),4),
            'time_rate': round(float((g.exit_reason=='TIME').mean()),4),
            'same_bar_ambiguity_count': int(g.same_bar_stop_target_ambiguity.sum()),
            'stop_gap_count': int(g.stop_gap_through.sum()),
            'nominal_stop_gt_2000_count': int((g.nominal_full_stop_usd>2000).sum()),
            'max_gap_between_signal_days': int(gaps.max()) if len(gaps) else 0,
            'gaps_gt7_days': int((gaps>7).sum()),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--zip',type=Path,required=True)
    p.add_argument('--h01',type=Path,required=True)
    p.add_argument('--h05',type=Path,required=True)
    p.add_argument('--h09',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    dates,arr,overnight,source=load_development(args.zip)
    raw=standardize(args.h01,args.h05,args.h09)
    eligible,excluded=prepare_events(raw,dates,arr)
    selected=(eligible.sort_values(['session','entry_ix','priority'],kind='stable')
        .drop_duplicates('session',keep='first'))
    trades=compute_trades(eligible,arr)
    summary=calc_summary(trades)
    portfolio=trades.merge(selected[['session','hypothesis']].assign(selected=True),
        on=['session','hypothesis'],how='inner')
    portfolio_summary=calc_summary(portfolio,hypothesis_col=False)
    overlap=eligible.groupby('session').hypothesis.nunique()
    raw_counts=raw.hypothesis.value_counts().to_dict()
    eligible_counts=eligible.hypothesis.value_counts().to_dict()
    selected_counts=selected.hypothesis.value_counts().to_dict()
    overview={
        'research_state':'POST_SELECTION_EXPLORATORY_ONLY_NOT_VALIDATED',
        'source':source,'data_years_read':[2020,2021,2022,2023,2024],
        'holdout_2025_opened':False,'holdout_2026_opened':False,
        'dataset':{'source_signal_counts':raw_counts,'eligible_signal_counts':eligible_counts,
          'excluded_signal_reasons':excluded,'eligible_signal_total':len(eligible),
          'days_with_at_least_2_distinct_hypotheses':int((overlap>=2).sum()),
          'days_with_at_least_3_distinct_hypotheses':int((overlap>=3).sum()),
          'portfolio_one_signal_per_day':len(selected),'portfolio_first_signal_counts':selected_counts},
        'execution':{'grids_per_hypothesis':len(STOPS)*len(TARGETS)*len(TIMEOUTS),
          'stop_fractions':STOPS,'target_r':TARGETS,'timeout_minutes':TIMEOUTS,
          'NQ_free_RT':FEES['NQ'],'MNQ_free_RT':FEES['MNQ'],
          'slippage_ticks_each_side':2,'fees_not_MFFU':True,
          'min_history_rth_sessions':14,'stop_target_same_bar':'STOP_FIRST'},
        'metrics':{'individual_strategy_scenarios':len(summary),
                   'portfolio_strategy_scenarios':len(portfolio_summary),
                   'executed_grid_trades':len(trades),
                   'signals_unchanged':True,'2025_confirmation_authorized':False},
        'notes':[
           'NQ price path for both NQ and synthetic MNQ; separately observed MNQ execution is not simulated',
           'Closed-trade max DD is not floating-equity EOD trailing drawdown',
           'This replay of hypotheses chosen after inspecting 2020-24 outcomes cannot validate discovery',
           'Results are a fixed engineering comparison, not statistically independent tests',
           'Bars are 1m OHLC; when SL and TP both hit, STOP is assumed first',
           'Unselected same-day strategy signals can strongly overlap and cannot be summed as a portfolio',
           'No 2025/2026 raw ZIP member was opened',
        ]}
    summary.to_csv(args.out/'INDIVIDUAL_4X18X2_SCENARIOS.csv',index=False)
    portfolio_summary.to_csv(args.out/'PORTFOLIO_18X2_SCENARIOS.csv',index=False)
    eligible.to_csv(args.out/'ELIGIBLE_ORIGINAL_SIGNALS.csv',index=False)
    selected.to_csv(args.out/'PORTFOLIO_FIRST_SIGNALS.csv',index=False)
    trades.to_csv(args.out/'FULL_EXECUTION_GRID_TRADES.csv.gz',index=False,compression='gzip')
    (args.out/'REPORT.json').write_text(json.dumps(overview,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(overview,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    main()