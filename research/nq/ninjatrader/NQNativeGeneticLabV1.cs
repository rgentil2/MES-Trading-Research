// S0.40/S0.41 - Native NinjaTrader 8 exploratory generator (V1; Standard M1).
// EVERYTHING - indicator calculations, structure optimization, orders, PnL - runs
// inside NinjaTrader 8. No Python signals, market data processing or CSV inputs.
//
// FIRST STAGE: two independently variable condition slots from 10 documented
// signal primitives, AND/OR combination, optional reversal, SL/TP parameters.
// The Strategy Analyzer's built-in DEFAULT or GENETIC optimizer explores these
// properties. These are structural combinations, not merely MA period tuning.
// Not 132/132 yet. No claim of 10k unique evaluated until NT8 results exist.
//
// S0.41 CHOICE: use NinjaTrader's OWN Standard M1 historical fill engine.
// No Python execution model or tick-source requirement for initial exploration.
 // STATUS: SOURCE-ONLY / NOT COMPILED IN NINJATRADER HERE / NO BACKTEST YET.
// TESTING ONLY. Before any use, NT8 must be configured with Eastern US time,
// original NQ 1-minute Last history / exact roll schedule, costs, and 2020-22
// IST only. Exit at 11:28 CLOSE -> next-bar entry/open near 11:29 (conservative
// variant; not yet identical to the frozen 11:29 bar-end exit).
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQNativeGeneticLabV1 : Strategy
    {
        private DateTime lastSession = DateTime.MinValue;
        private int barsThisSession = 0;
        private int entrySubmissionsToday = 0;
        private double firstClosedCumProfit = 0.0;

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
                Name = "NQNativeGeneticLabV1";
                Description = "Native strategy structure generator via NT8 Genetic/Default optimizer. Research only.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.UniqueEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 3;
                IncludeTradeHistoryInBacktest = true;
                // Explicit native Strategy Analyzer baseline. Costs are
                // provided by the NT8 NQ commission template, NOT Python.
                // Standard fill simulates OHLC-based virtual intrabar steps.
                OrderFillResolution = OrderFillResolution.Standard;
                IsFillLimitOnTouch = false;
                IncludeCommission = true;
                Slippage = 2; // per eligible simulated fill, limited by NT8 bar range
                StartBehavior = StartBehavior.WaitUntilFlat;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;

                AType = 0; APeriod = 12;
                BType = 7; BPeriod = 14;
                CombineMode = 0; ReverseSignals = 0;
                StopTicks = 20; TargetTicks = 32;
                MaxDailyEntrySubmissions = 2;
            }
            else if (State == State.Configure)
            {
                // Native NT8 protective orders are submitted from executions.
                // SetStopLoss / SetProfitTarget must be configured pre-entry.
                SetStopLoss(CalculationMode.Ticks, StopTicks);
                if (TargetTicks > 0)
                    SetProfitTarget(CalculationMode.Ticks, TargetTicks);
            }
        }

        // Types: 0 SMA slope; 1 EMA slope; 2 WMA slope; 3 RSI slope;
        // 4 CCI slope; 5 Close vs SMA; 6 Close vs EMA;
        // 7 RSI > 55 / < 45; 8 CCI > 100 / < -100;
        // 9 SMA versus EMA crossover (fast n, slow 2*n).
        // Each pair (bull,bear) has explicit mutually exclusive behavior.
        private void EvaluateSlot(int type, int n, out bool bull, out bool bear)
        {
            bull = false;
            bear = false;
            double current, previous;

            switch (type)
            {
                case 0:
                    current = SMA(Close, n)[0];
                    previous = SMA(Close, n)[1];
                    bull = current > previous; bear = current < previous;
                    break;
                case 1:
                    current = EMA(Close, n)[0];
                    previous = EMA(Close, n)[1];
                    bull = current > previous; bear = current < previous;
                    break;
                case 2:
                    current = WMA(Close, n)[0];
                    previous = WMA(Close, n)[1];
                    bull = current > previous; bear = current < previous;
                    break;
                case 3:
                    current = RSI(Close, n, 3)[0];
                    previous = RSI(Close, n, 3)[1];
                    bull = current > previous; bear = current < previous;
                    break;
                case 4:
                    current = CCI(Close, n)[0];
                    previous = CCI(Close, n)[1];
                    bull = current > previous; bear = current < previous;
                    break;
                case 5:
                    current = SMA(Close, n)[0];
                    bull = Close[0] > current; bear = Close[0] < current;
                    break;
                case 6:
                    current = EMA(Close, n)[0];
                    bull = Close[0] > current; bear = Close[0] < current;
                    break;
                case 7:
                    current = RSI(Close, n, 3)[0];
                    bull = current > 55.0; bear = current < 45.0;
                    break;
                case 8:
                    current = CCI(Close, n)[0];
                    bull = current > 100.0; bear = current < -100.0;
                    break;
                case 9:
                    int slow = Math.Min(240, n * 2);
                    current = SMA(Close, n)[0] - EMA(Close, slow)[0];
                    previous = SMA(Close, n)[1] - EMA(Close, slow)[1];
                    bull = previous <= 0.0 && current > 0.0;
                    bear = previous >= 0.0 && current < 0.0;
                    break;
                default:
                    // Fail closed: unknown generator gene never trades.
                    break;
            }
        }

        private int NeededBars(int type, int n)
        {
            // Conservative INTRA-session completed bar warmup (RTH only).
            // Long periods may never activate by 11:27; that is honest.
            return type == 9 ? (2 * n + 4) : (n + 4);
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
            if (AType < 0 || AType > 9 || BType < 0 || BType > 9 ||
                APeriod < 2 || BPeriod < 2 || APeriod > 117 || BPeriod > 117 ||
                CombineMode < 0 || CombineMode > 1 ||
                ReverseSignals < 0 || ReverseSignals > 1)
                return;
            if (barsThisSession < Math.Max(NeededBars(AType, APeriod),
                                           NeededBars(BType, BPeriod)))
                return;

            if (Position.MarketPosition != MarketPosition.Flat ||
                entrySubmissionsToday >= MaxDailyEntrySubmissions)
                return;

            // Research-only approximate risk gate; not the funded program rule.
            if (StopTicks * DollarPerTick + AdverseStopSlipTickReserve * DollarPerTick
                + ProvisionalRoundTripFeeUsd > 300.0)
                return;

            double closedToday =
                SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit -
                firstClosedCumProfit;
            if (closedToday <= -600.0)
                return;

            bool aBull, aBear, bBull, bBear;
            EvaluateSlot(AType, APeriod, out aBull, out aBear);
            EvaluateSlot(BType, BPeriod, out bBull, out bBear);

            bool bull = CombineMode == 0 ? (aBull && bBull) : (aBull || bBull);
            bool bear = CombineMode == 0 ? (aBear && bBear) : (aBear || bBear);

            // OR conflicts do not generate trades.
            if (bull == bear)
                return;

            if (ReverseSignals == 1)
            {
                bool oldBull = bull;
                bull = bear; bear = oldBull;
            }

            if (bull)
                EnterLong(1, LongTag);
            else
                EnterShort(1, ShortTag);

            // Counts attempted entries rather than broker-executed fills;
            // this prototype ONLY submits market orders.
            entrySubmissionsToday++;
        }

        // Every property below becomes an optimization "gene" inside NT8.
        // Genetic optimizer can vary BOTH indicator types, BOTH periods,
        // expression structure (AND/OR), direction and the exit parameters.
        // Ranges are intentionally documented and reversible to a genome.
        [NinjaScriptProperty]
        [Range(0, 9)]
        [Display(Name = "A type (0..9)", GroupName = "01 Generation", Order = 1)]
        public int AType { get; set; }

        [NinjaScriptProperty]
        [Range(2, 117)]
        [Display(Name = "A period", GroupName = "01 Generation", Order = 2)]
        public int APeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, 9)]
        [Display(Name = "B type (0..9)", GroupName = "01 Generation", Order = 3)]
        public int BType { get; set; }

        [NinjaScriptProperty]
        [Range(2, 117)]
        [Display(Name = "B period", GroupName = "01 Generation", Order = 4)]
        public int BPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, 1)]
        [Display(Name = "AND=0 OR=1", GroupName = "01 Generation", Order = 5)]
        public int CombineMode { get; set; }

        [NinjaScriptProperty]
        [Range(0, 1)]
        [Display(Name = "Reverse (0/1)", GroupName = "01 Generation", Order = 6)]
        public int ReverseSignals { get; set; }

        [NinjaScriptProperty]
        [Range(1, 55)]
        [Display(Name = "Stop ticks", GroupName = "02 Exits", Order = 7)]
        public int StopTicks { get; set; }

        [NinjaScriptProperty]
        [Range(0, 240)]
        [Display(Name = "Target ticks (0=none)", GroupName = "02 Exits", Order = 8)]
        public int TargetTicks { get; set; }

        [NinjaScriptProperty]
        [Range(1, 2)]
        [Display(Name = "Max daily entry submissions", GroupName = "03 Risk", Order = 9)]
        public int MaxDailyEntrySubmissions { get; set; }
    }
}
