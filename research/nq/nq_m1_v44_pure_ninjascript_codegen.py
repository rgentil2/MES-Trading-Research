#!/usr/bin/env python3
"""S0.39: PURE AST -> native NinjaTrader 8 NinjaScript code generator.

Python NEVER reads market OHLC, computes indicator values, emits timed signal
CSV, backtests a strategy, or calculates any fitness here. NinjaScript alone
will evaluate indicators and enter/exit inside NinjaTrader Strategy Analyzer.

CURRENT EXPLICITLY LIMITED BACKEND: SMA/EMA/WMA on CLOSE only; MARKET entry;
required FIXED_POINTS stop; optional FIXED_POINTS/R_MULTIPLE target; no dynamic
trailing, breakeven or exit_after_bars. Unsupported frozen ASTs cause a HARD
ERROR. The backend is a portable proof-of-architecture, NOT a 132/132 port.
NinjaTrader compiler/runtime is NOT available in the GitHub Python CI.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import re
from research.nq.nq_m1_v26_structural_generator import LEVEL_OPS,LAG_OPS,sha

_SUPPORTED_INDICATORS={"SMA":"SMA","EMA":"EMA","WMA":"WMA"}
_ALLOWED_PREDICATES=set(LEVEL_OPS)|set(LAG_OPS)
_ID=re.compile(r"^NQ26_[0-9a-f]{16}$")
_NAME=re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,75}$")
POINT_VALUE=20.0
TICK=0.25
INITIAL_RISK_CEILING=300.0
ESTIMATED_COMMISSION_RT=4.68
ESTIMATED_STOP_SLIP_TICKS=2

class UnsupportedNinjaScriptAST(ValueError):
    pass

def _num(v):
    if isinstance(v,bool) or not isinstance(v,(int,float)):
        raise UnsupportedNinjaScriptAST("Expected numeric AST parameter")
    import math
    if not math.isfinite(v):raise UnsupportedNinjaScriptAST("Nonfinite")
    return format(v,".12g")

def _int(v,lower=1,upper=10000):
    if type(v) is not int or not lower<=v<=upper:
        raise UnsupportedNinjaScriptAST("AST integer/period outside supported range")
    return v

def _indicator(block):
    if not isinstance(block,dict):raise UnsupportedNinjaScriptAST("Missing indicator block")
    name=block.get("name");params=block.get("parameters")
    if name not in _SUPPORTED_INDICATORS:
        raise UnsupportedNinjaScriptAST(f"Indicator {name!r} requires native C# implementation")
    if set(params or {})!={"period","source"} or params["source"]!="close":
        raise UnsupportedNinjaScriptAST(f"{name}: only native Close source currently audited")
    period=_int(params["period"],2,240)
    if "output" in block:
        raise UnsupportedNinjaScriptAST("Multi-line output not implemented")
    return f"{_SUPPORTED_INDICATORS[name]}(Close, {period})",period

def _leaf(x):
    if not isinstance(x,dict) or x.get("op") not in _ALLOWED_PREDICATES:
        raise UnsupportedNinjaScriptAST("Unsupported leaf operator")
    src,n=_indicator(x["indicator"])
    op=x["op"]
    if op in LEVEL_OPS:
        if set(x)!={"indicator","op","threshold"}:
            raise UnsupportedNinjaScriptAST("Unrecognized level leaf fields")
        t=_num(x["threshold"])
        now=f"{src}[0]"
        if op=="ABOVE_LEVEL":return f"({now} > {t})",n
        if op=="BELOW_LEVEL":return f"({now} < {t})",n
        if op=="CROSS_ABOVE_LEVEL":
            return f"({src}[1] <= {t} && {now} > {t})",n+1
        return f"({src}[1] >= {t} && {now} < {t})",n+1
    if set(x)!={"indicator","op","lag_completed_bars"}:
        raise UnsupportedNinjaScriptAST("Unrecognized lag leaf fields")
    lag=_int(x["lag_completed_bars"],1,20)
    cur=f"{src}[0]";old=f"{src}[{lag}]"
    if op in ("RISING","ABOVE_LAG"):return f"({cur} > {old})",n+lag
    if op in ("FALLING","BELOW_LAG"):return f"({cur} < {old})",n+lag
    if op=="CROSSES_OWN_LAG":
        return f"({src}[1] <= {src}[{lag+1}] && {cur} > {old})",n+lag+1
    raise UnsupportedNinjaScriptAST(op)

def _expr(tree):
    if not isinstance(tree,dict):raise UnsupportedNinjaScriptAST("AST expression must be dictionary")
    if tree.get("op") in ("AND","OR"):
        if set(tree)!={"op","left","right"}:
            raise UnsupportedNinjaScriptAST("Unknown binary branch properties")
        a,na=_expr(tree["left"]);b,nb=_expr(tree["right"])
        op="&&" if tree["op"]=="AND" else "||"
        return f"({a} {op} {b})",max(na,nb)
    return _leaf(tree)

def _settings(ast):
    if not isinstance(ast,dict) or not _ID.fullmatch(ast.get("id","")):
        raise UnsupportedNinjaScriptAST("Frozen NQ26 identity required")
    if ast["id"]!="NQ26_"+sha(ast)[:16]:
        raise UnsupportedNinjaScriptAST("Frozen AST id/SHA must match canonical content")
    if (ast.get("schema")!="NQ_M1_V26_AST_PRE_ECONOMIC"
        or ast.get("universe")!="NQ_M1"
        or ast.get("position_sizing")!={"instrument":"NQ","contracts":1}
        or ast.get("signal_clock")!="America/New_York"
        or ast.get("market_data_years_permitted_for_discovery")!=[2020,2021,2022]
        or ast.get("bars_are_end_labeled") is not True
        or ast.get("signal_uses_completed_bars_only") is not True):
        raise UnsupportedNinjaScriptAST("Wrong instrument, clock, cohort or price-data years")
    entry=ast["entry_order"];end=ast["exit"]
    if entry!={"kind":"MARKET","offset_ticks":0,"expiry_bars":1}:
        raise UnsupportedNinjaScriptAST("LIMIT/STOP/pending entries not translated yet")
    if (end.get("trailing") is not None or end.get("break_even") is not None
        or end.get("exit_after_bars") is not None or end.get("flat_at_et")!="11:29"):
        raise UnsupportedNinjaScriptAST("Trailing/BE/bar exits not translated yet")
    stop=end["stop_loss_required"];tp=end["profit_target"]
    if stop.get("kind")!="FIXED_POINTS" or set(stop)!={"kind","points"}:
        raise UnsupportedNinjaScriptAST("Native codegen requires FIXED_POINTS SL")
    stop_ticks=round(float(stop["points"])/TICK)
    if abs(stop_ticks*TICK-stop["points"])>1e-9 or not 1<=stop_ticks<=1200:
        raise UnsupportedNinjaScriptAST("Stop loss must be positive NQ tick grid")
    if (stop_ticks*TICK*POINT_VALUE+ESTIMATED_STOP_SLIP_TICKS*TICK*POINT_VALUE
        +ESTIMATED_COMMISSION_RT)>INITIAL_RISK_CEILING:
        raise UnsupportedNinjaScriptAST("Stop exceeds provisional $300 cap before order")
    if tp["kind"]=="NONE" and set(tp)=={"kind"}:tp_ticks=None
    elif tp["kind"]=="FIXED_POINTS" and set(tp)=={"kind","points"}:
        raw=float(tp["points"])/TICK;tp_ticks=round(raw)
        if abs(tp_ticks-raw)>1e-9 or tp_ticks<1:
            raise UnsupportedNinjaScriptAST("Target must be positive NQ tick grid")
    elif tp["kind"]=="R_MULTIPLE" and set(tp)=={"kind","risk_multiple"}:
        raw=stop_ticks*float(tp["risk_multiple"]);tp_ticks=round(raw)
        if abs(tp_ticks-raw)>1e-9 or tp_ticks<1:
            raise UnsupportedNinjaScriptAST("R-multiple target must resolve to exact NQ tick")
    else:raise UnsupportedNinjaScriptAST("Unsupported profit target")
    if tp_ticks is not None and tp_ticks>20000:
        raise UnsupportedNinjaScriptAST("Excessive target")
    return stop_ticks,tp_ticks

def compile_ninjascript(ast,classname=None):
    """Returns a full NinjaScript Strategy .cs source, NOT signals or performance."""
    stop_ticks,tp_ticks=_settings(ast)
    lo,lo_warm=_expr(ast["long"])
    sh,sh_warm=_expr(ast["short"])
    warm=max(lo_warm,sh_warm)+2
    default_name="NQAST_"+ast["id"][5:]
    classname=default_name if classname is None else classname
    if not _NAME.fullmatch(classname):
        raise UnsupportedNinjaScriptAST("Unsafe C# class name")
    target_line=(f"SetProfitTarget(CalculationMode.Ticks, {tp_ticks});"
                 if tp_ticks is not None else "// No profit target for this AST")
    return f'''// GENERATED BY Python AS A CODE WRITER ONLY. Price calculations are 100% NinjaScript.
// AST {ast["id"]}; this is a limited transpilation, NOT NT8-compiled or validated.
// REQUIRES: NQ 1-minute Last and NY time zone in NinjaTrader Strategy Analyzer.
// RESTRICT date selection in Strategy Analyzer to 2020-2022 (IST); do not open holdouts.
// Native OnBarClose orders fill on subsequent historical bar; note fill caveats.
// A flat command at 11:28 close is submitted for next bar open (~11:29),
// intentionally conservative/early vs original 11:29 end-bar flat policy.
// Do NOT use for funded account execution or portfolio finalization yet.
using System;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{{
    public class {classname} : Strategy
    {{
        private DateTime currentDate = DateTime.MinValue;
        private int submittedToday = 0;
        private double dayOpeningCumProfit = 0.0;
        private const string LongTag = "{classname}_L";
        private const string ShortTag = "{classname}_S";

        protected override void OnStateChange()
        {{
            if (State == State.SetDefaults)
            {{
                Name = "{classname}";
                Description = "Generated NQ AST; ALL calculations/execution inside NinjaTrader.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.UniqueEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                BarsRequiredToTrade = {warm};
            }}
            else if (State == State.Configure)
            {{
                SetStopLoss(CalculationMode.Ticks, {stop_ticks});
                {target_line}
            }}
        }}

        protected override void OnBarUpdate()
        {{
            if (BarsInProgress != 0 || CurrentBar < {warm})
                return;
            if (BarsPeriod.BarsPeriodType != BarsPeriodType.Minute || BarsPeriod.Value != 1)
                return;
            if (Instrument.MasterInstrument.Name != "NQ")
                return;
            // Fail closed if an unintended calendar year was selected.
            if (Time[0].Year < 2020 || Time[0].Year > 2022)
                return;
            if (Time[0].Date != currentDate)
            {{
                currentDate = Time[0].Date;
                submittedToday = 0;
                dayOpeningCumProfit = SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit;
            }}
            int clock = ToTime(Time[0]);
            // Submit early so the next historical bar's open is approx. 11:29 ET.
            if (clock >= 112800)
            {{
                if (Position.MarketPosition == MarketPosition.Long)
                    ExitLong("NY_Flat_L", LongTag);
                else if (Position.MarketPosition == MarketPosition.Short)
                    ExitShort("NY_Flat_S", ShortTag);
                return;
            }}
            if (clock < 93500 || clock > 112700)
                return;
            if (Position.MarketPosition != MarketPosition.Flat || submittedToday >= 2)
                return;
            // CLOSED-trade pause only; exact funded trailing/equity risk NOT validated.
            double realizedToday = SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit
                                   - dayOpeningCumProfit;
            if (realizedToday <= -600.0)
                return;

            bool longSignal = {lo};
            bool shortSignal = {sh};
            // Conflict = no entry; never reverse an open position.
            if (longSignal == shortSignal)
                return;
            if (longSignal)
                EnterLong(1, LongTag);
            else
                EnterShort(1, ShortTag);
            // Counts submitted orders, NOT executions: conservative temporary cap.
            submittedToday++;
        }}
    }}
}}
'''

def export(asts,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    for ast in asts:
        # Fail closed BEFORE writing any output, avoid half-generated campaigns.
        results.append((ast,compile_ninjascript(ast)))
    manifest=[]
    for ast,code in results:
        cls="NQAST_"+ast["id"][5:]
        file=out/(cls+".cs")
        file.write_text(code,encoding="utf8")
        import hashlib
        manifest.append({"ast_id":ast["id"],"ninjascript_class":cls,
                         "code_sha256":hashlib.sha256(code.encode()).hexdigest(),
                         "file":file.name})
    (out/"manifest.json").write_text(json.dumps({
        "schema":"NQ_NT8_PURE_NINJASCRIPT_CODEGEN_PROTOTYPE_V1",
        "scope":"SMA_EMA_WMA_CLOSE_MARKET_FIXED_STOP_ONLY",
        "all_formula_values_computed_inside_ninjatrader":True,
        "python_market_data_loaded":False,
        "python_signal_series_exported":False,
        "python_backtests_run":False,
        "supported_all_132":False,
        "NT8_compilation_verified":False,
        "funnel_fitness_or_winner_selected":False,
        "artifacts":manifest},indent=2,sort_keys=True)+"\n")
    return manifest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ast-json",required=True,type=Path)
    parser.add_argument("--out-dir",required=True,type=Path)
    args=parser.parse_args()
    data=json.loads(args.ast_json.read_text())
    asts=data if isinstance(data,list) else [data]
    print(json.dumps(export(asts,args.out_dir),indent=2))

if __name__=="__main__":main()
