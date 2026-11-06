// S0.71 V11 — research-only NQ historical strategy. Derived by freezing
// the proven V5 order, exit, cost and risk contract and replacing ONLY
// the signal interpretation / 2020–22 RTH signal-bar input window.
// 132 CONDITIONS, not 132 independent technical indicators. NOT LIVE READY.
// IMPORTANT: No NT8 runtime compile/backtest parity claim.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQNativeSignalLabV11 : Strategy
    {
        private readonly List<NQBarV11> rthBars = new List<NQBarV11>();
        private DateTime lastSession = DateTime.MinValue;
        private int barsThisSession = 0;
        private int entrySubmissionsToday = 0;
        private double firstClosedCumProfit = 0.0;

        // Read by NQNativeStructureFitnessV3. Not NinjaScriptProperty genes.
        [Browsable(false)]
        [XmlIgnore]
        public bool CanonicalReady { get; private set; }
        [Browsable(false)]
        [XmlIgnore]
        public bool IsStructurallyRedundant { get; private set; }
        [Browsable(false)]
        [XmlIgnore]
        public int EffectiveConditionCount { get; private set; }
        [Browsable(false)]
        [XmlIgnore]
        public string CanonicalRuntimeFingerprint { get; private set; }
        [Browsable(false)]
        [XmlIgnore]
        public string CanonicalBooleanKey { get; private set; }

        private const string LongTag  = "GEN_LONG";
        private const string ShortTag = "GEN_SHORT";
        private const int FirstSignalHHmmss = 93500;
        private const int LastSignalHHmmss = 112700;
        private const int FlatSubmitHHmmss = 112800;
        private const double DollarPerTick = 5.00;
        private const double ProvisionalRoundTripFeeUsd = 4.68;
        private const double AdverseStopSlipTickReserve = 2.0;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "NQNativeSignalLabV11";
                Description = "NQ V11 native 132 OHLCV conditions / 12 features, fixed+ATR exits; historical research only.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.UniqueEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 3;
                IncludeTradeHistoryInBacktest = true;
                IsInstantiatedOnEachOptimizationIteration = true;
                // Explicit native Strategy Analyzer baseline. Costs are
                // provided by the NT8 NQ commission template, NOT Python.
                // Standard fill simulates OHLC-based virtual intrabar steps.
                OrderFillResolution = OrderFillResolution.Standard;
                IsFillLimitOnTouch = false;
                IncludeCommission = true;
                Slippage = 2; // per eligible simulated fill, limited by NT8 bar range
                StartBehavior = StartBehavior.WaitUntilFlat;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;

                ConditionCount = 2;
                AType = 0; APeriod = 12;
                BType = 44; BPeriod = 12;
                CType = 77; CPeriod = 12;
                DType = 121; DPeriod = 12;
                CombineAB = 0; CombineBC = 0; CombineCD = 0;
                ReverseSignals = 0;
                // Keep V1's technical SL/TP defaults for 2-slot comparison.
                // Dynamic ATR SL/TP will be a separate, explicitly reviewed version.
                StopTicks = 20; TargetTicks = 32;
                MaxDailyEntrySubmissions = 2;
                ExitMode = 0; ATRPeriod = 14;
                ATRStopX10 = 15; ATRTargetX10 = 25;
                CanonicalReady = false;
                IsStructurallyRedundant = true; // fail closed until analysis
                EffectiveConditionCount = 0;
                CanonicalRuntimeFingerprint = "";
                CanonicalBooleanKey = "";
            }
            else if (State == State.DataLoaded)
            {
                rthBars.Clear();
                // Each Genetic iteration has an independent Strategy instance.
                // Compute at DataLoaded so all 16 optimization gene values are
                // fixed. No global state or cross-run cache is used.
                CanonicalReady = false;
                IsStructurallyRedundant = true;
                try
                {
                    var k = NQNativeExitCanonicalV11.Analyze(V11Genes());
                    CanonicalBooleanKey = k.BooleanKey;
                    CanonicalRuntimeFingerprint = k.Fingerprint;
                    EffectiveConditionCount = k.EffectiveLeaves;
                    IsStructurallyRedundant = k.IsRedundant;
                    CanonicalReady = true;
                }
                catch (ArgumentException ex)
                {
                    // Malformed optimizer genes: fitness rejects candidate.
                    Print("NQ_V11_EXIT_REJECT invalid-gene " + ex.Message);
                }
                // Diagnostic emitted by the actual historical strategy
                // instance, not by the configuration UI/SetDefaults.
                // During a Genetic run this is one line per iteration:
                // informational only, not proof of unique evaluations.
                Print("NQ_V11_EXIT_RUNTIME"
                    + " ready=" + CanonicalReady
                    + " redundant=" + IsStructurallyRedundant
                    + " effective=" + EffectiveConditionCount
                    + " id=" + CanonicalRuntimeFingerprint
                    + " bool=" + CanonicalBooleanKey);
            }
            else if (State == State.Configure)
            {
                // Native NT8 protective orders are submitted from executions.
                // SetStopLoss / SetProfitTarget must be configured pre-entry.
                // Mode0 is IDENTICAL to the V3 protective order setup.
                if (ExitMode == 0)
                {
                    SetStopLoss(CalculationMode.Ticks, StopTicks);
                    if (TargetTicks > 0)
                        SetProfitTarget(CalculationMode.Ticks, TargetTicks);
                }
                else if (ExitMode == 1 && TargetTicks > 0)
                {
                    // Fixed target with ATR stop calculated just before entry.
                    SetProfitTarget(CalculationMode.Ticks, TargetTicks);
                }
                // Modes 2/3 deliberately do not register a global fixed TP.
                // Dynamic protective orders are attached by entry signal
                // BEFORE submitting a market entry, not after the fill.
            }
        }

        private int[] V11Genes()
        {
            return new int[] {
                ConditionCount, AType, APeriod, BType, BPeriod,
                CType, CPeriod, DType, DPeriod,
                CombineAB, CombineBC, CombineCD, ReverseSignals,
                StopTicks, TargetTicks, MaxDailyEntrySubmissions,
                ExitMode, ATRPeriod, ATRStopX10, ATRTargetX10
            };
        }

        // 12 genuinely different OHLCV features x 11 predicates. Each
        // directional signal is evaluated on CLOSED RTH M1 bars only.
        private void EvaluateSlot(int type, int n, out bool bull, out bool bear)
        {
            NQNativeConditionsV11.TryEvaluate(rthBars,type,n,out bull,out bear);
        }

        private int NeededBars(int type,int n)
        {
            return NQNativeConditionsV11.RequiredBars(n);
        }

        protected override void OnBarUpdate()
        {
            // This initial research strategy is NEVER intended to submit
            // live orders. Historical Strategy Analyzer passes only.
            if (State != State.Historical)
                return;
            if (BarsInProgress != 0)
                return;

            // All signals, calculations and fills are NATIVELY inside NT8.
            if (BarsPeriod.BarsPeriodType != BarsPeriodType.Minute ||
                BarsPeriod.Value != 1 || Instrument.MasterInstrument.Name != "NQ")
                return;

            if (Time[0].Date != lastSession)
            {
                lastSession = Time[0].Date;
                rthBars.Clear();
                barsThisSession = 0;
                entrySubmissionsToday = 0;
                firstClosedCumProfit = SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit;
            }
            else
                barsThisSession++;

            // No IST backtest may score held-out 2023/24/25/26.
            // The Strategy Analyzer's date selection MUST also be 2020-22.
            if (Time[0].Year < 2020 || Time[0].Year > 2022)
                return;

            int hhmmss = ToTime(Time[0]);
            // Completed 09:30–11:27 Eastern minute bars; no overnight input.
            // Clearing by calendar date avoids cross-session data leakage.
            if(hhmmss>=93000 && hhmmss<=112700)
                rthBars.Add(new NQBarV11(Open[0],High[0],Low[0],
                    Close[0],Volume[0]));
            if (CurrentBar < 3)
                return;

            // A market flat order submitted at 11:28 close is normally filled
            // on the next historical bar; approx. 11:29 OPEN, not 11:29 CLOSE.
            if (hhmmss >= FlatSubmitHHmmss)
            {
                if (Position.MarketPosition == MarketPosition.Long)
                    ExitLong("EXIT_1129_L", LongTag);
                else if (Position.MarketPosition == MarketPosition.Short)
                    ExitShort("EXIT_1129_S", ShortTag);
                return;
            }

            if (hhmmss < FirstSignalHHmmss || hhmmss > LastSignalHHmmss)
                return;
            if (ConditionCount < 1 || ConditionCount > 4 ||
                AType < 0 || AType >= NQNativeConditionsV11.Count || APeriod < 4 || APeriod > 30 ||
                (ConditionCount >= 2 && (BType < 0 || BType >= NQNativeConditionsV11.Count ||
                  BPeriod < 4 || BPeriod > 30 || CombineAB < 0 || CombineAB > 1)) ||
                (ConditionCount >= 3 && (CType < 0 || CType >= NQNativeConditionsV11.Count ||
                  CPeriod < 4 || CPeriod > 30 || CombineBC < 0 || CombineBC > 1)) ||
                (ConditionCount >= 4 && (DType < 0 || DType >= NQNativeConditionsV11.Count ||
                  DPeriod < 4 || DPeriod > 30 || CombineCD < 0 || CombineCD > 1)) ||
                ReverseSignals < 0 || ReverseSignals > 1 ||
                StopTicks < 1 || TargetTicks < 0 ||
                MaxDailyEntrySubmissions < 1 || MaxDailyEntrySubmissions > 2 ||
                ExitMode < 0 || ExitMode > 3 || ATRPeriod < 7 || ATRPeriod > 28 ||
                ATRStopX10 < 10 || ATRStopX10 > 30 ||
                ATRTargetX10 < 10 || ATRTargetX10 > 50 ||
                (ExitMode == 1 && TargetTicks < 1))
                return;
            int required = NeededBars(AType, APeriod);
            if (ConditionCount >= 2) required = Math.Max(required, NeededBars(BType, BPeriod));
            if (ConditionCount >= 3) required = Math.Max(required, NeededBars(CType, CPeriod));
            if (ConditionCount >= 4) required = Math.Max(required, NeededBars(DType, DPeriod));
            if (ExitMode > 0)
                required = Math.Max(required, ATRPeriod + 4);
            if (rthBars.Count < required)
                return;

            if (Position.MarketPosition != MarketPosition.Flat ||
                entrySubmissionsToday >= MaxDailyEntrySubmissions)
                return;

            // ATR is sampled at the COMPLETED signal bar [0], no future
            // fill bar price or indicator values are used. Native NT8 fills
            // the entry on the next historical bar. Quantize to whole ticks.
            int intendedStopTicks, intendedTargetTicks;
            double completedSignalAtr = ExitMode == 0 ? 0.0 : ATR(ATRPeriod)[0];
            if (!NQNativeATRExitMathV5.TryCompute(ExitMode,
                    completedSignalAtr, TickSize, StopTicks, TargetTicks,
                    ATRStopX10, ATRTargetX10,
                    out intendedStopTicks, out intendedTargetTicks))
                return;

            // Research-only approximate pre-order risk gate, NOT a
            // complete funded-account intrabar/trailing drawdown model.
            if (intendedStopTicks * DollarPerTick +
                AdverseStopSlipTickReserve * DollarPerTick +
                ProvisionalRoundTripFeeUsd > 300.0)
                return;

            double closedToday =
                SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit -
                firstClosedCumProfit;
            if (closedToday <= -600.0)
                return;

            bool bull, bear;
            EvaluateSlot(AType, APeriod, out bull, out bear);
            if (ConditionCount >= 2)
            {
                bool bBull, bBear;
                EvaluateSlot(BType, BPeriod, out bBull, out bBear);
                bull = CombineAB == 0 ? (bull && bBull) : (bull || bBull);
                bear = CombineAB == 0 ? (bear && bBear) : (bear || bBear);
            }
            if (ConditionCount >= 3)
            {
                bool cBull, cBear;
                EvaluateSlot(CType, CPeriod, out cBull, out cBear);
                bull = CombineBC == 0 ? (bull && cBull) : (bull || cBull);
                bear = CombineBC == 0 ? (bear && cBear) : (bear || cBear);
            }
            if (ConditionCount >= 4)
            {
                bool dBull, dBear;
                EvaluateSlot(DType, DPeriod, out dBull, out dBear);
                bull = CombineCD == 0 ? (bull && dBull) : (bull || dBull);
                bear = CombineCD == 0 ? (bear && dBear) : (bear || dBear);
            }

            // OR conflicts do not generate trades.
            if (bull == bear)
                return;

            if (ReverseSignals == 1)
            {
                bool oldBull = bull;
                bull = bear; bear = oldBull;
            }

            // Set protective offsets BEFORE the entry submission.
            // Each ATR entry completely overrides its own stop/target;
            // thus no previous trade's dynamic offset can leak to a new one.
            if (ExitMode > 0)
            {
                string signal = bull ? LongTag : ShortTag;
                SetStopLoss(signal, CalculationMode.Ticks,
                    intendedStopTicks, false);
                if (ExitMode == 2)
                    SetProfitTarget(signal, CalculationMode.Ticks,
                        intendedTargetTicks);
            }
            if (bull)
                EnterLong(1, LongTag);
            else
                EnterShort(1, ShortTag);

            // Counts attempted entries rather than broker-executed fills;
            // this prototype ONLY submits market orders.
            entrySubmissionsToday++;
        }

        // Every property is an optimizer gene. V3 exposes canonical signature
        // for fitness inspection but DOES NOT change order/signal mechanics:
        // selecting the custom V3 fitness penalizes redundant structures.
        // MaxNetProfit would NOT respect that filter.
        [NinjaScriptProperty]
        [Range(1, 4)]
        [Display(Name = "Condition count (1..4)", GroupName = "01 Generation", Order = 1)]
        public int ConditionCount { get; set; }

        [NinjaScriptProperty]
        [Range(0, 131)]
        [Display(Name = "A condition (0..131)", GroupName = "01 Generation", Order = 2)]
        public int AType { get; set; }

        [NinjaScriptProperty]
        [Range(4, 30)]
        [Display(Name = "A period", GroupName = "01 Generation", Order = 3)]
        public int APeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, 131)]
        [Display(Name = "B condition (0..131)", GroupName = "01 Generation", Order = 4)]
        public int BType { get; set; }

        [NinjaScriptProperty]
        [Range(4, 30)]
        [Display(Name = "B period", GroupName = "01 Generation", Order = 5)]
        public int BPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, 131)]
        [Display(Name = "C condition (0..131)", GroupName = "01 Generation", Order = 6)]
        public int CType { get; set; }

        [NinjaScriptProperty]
        [Range(4, 30)]
        [Display(Name = "C period", GroupName = "01 Generation", Order = 7)]
        public int CPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, 131)]
        [Display(Name = "D condition (0..131)", GroupName = "01 Generation", Order = 8)]
        public int DType { get; set; }

        [NinjaScriptProperty]
        [Range(4, 30)]
        [Display(Name = "D period", GroupName = "01 Generation", Order = 9)]
        public int DPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, 1)]
        [Display(Name = "AB (AND=0 OR=1)", GroupName = "01 Generation", Order = 10)]
        public int CombineAB { get; set; }

        [NinjaScriptProperty]
        [Range(0, 1)]
        [Display(Name = "BC (AND=0 OR=1)", GroupName = "01 Generation", Order = 11)]
        public int CombineBC { get; set; }

        [NinjaScriptProperty]
        [Range(0, 1)]
        [Display(Name = "CD (AND=0 OR=1)", GroupName = "01 Generation", Order = 12)]
        public int CombineCD { get; set; }

        [NinjaScriptProperty]
        [Range(0, 1)]
        [Display(Name = "Reverse (0/1)", GroupName = "01 Generation", Order = 13)]
        public int ReverseSignals { get; set; }

        [NinjaScriptProperty]
        [Range(1, 55)]
        [Display(Name = "Stop ticks", GroupName = "02 Exits", Order = 14)]
        public int StopTicks { get; set; }

        [NinjaScriptProperty]
        [Range(0, 240)]
        [Display(Name = "Target ticks (0=none)", GroupName = "02 Exits", Order = 15)]
        public int TargetTicks { get; set; }

        [NinjaScriptProperty]
        [Range(1, 2)]
        [Display(Name = "Max daily entry submissions", GroupName = "03 Risk", Order = 16)]
        public int MaxDailyEntrySubmissions { get; set; }
        [NinjaScriptProperty]
        [Range(0, 3)]
        [Display(Name = "Exit mode (0..3)", GroupName = "03 Exits V5", Order = 1)]
        public int ExitMode { get; set; }

        [NinjaScriptProperty]
        [Range(7, 28)]
        [Display(Name = "ATR period", GroupName = "03 Exits V5", Order = 2)]
        public int ATRPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(10, 30)]
        [Display(Name = "ATR stop x10", GroupName = "03 Exits V5", Order = 3)]
        public int ATRStopX10 { get; set; }

        [NinjaScriptProperty]
        [Range(10, 50)]
        [Display(Name = "ATR target x10", GroupName = "03 Exits V5", Order = 4)]
        public int ATRTargetX10 { get; set; }

    }
}
