// S0.41 - Native NinjaTrader 8 NQ M1 source audit; ZERO ORDERS.
// Use directly in Strategy Analyzer with 1 Minute NQ Last, Eastern Time,
// and the RTH session template. This is a data/scheduling diagnostic,
// NOT an optimizer, backtest winner, imported-data transformer or account.
using System;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQNativeM1DataAuditV1 : Strategy
    {
        private DateTime activeDay = DateTime.MinValue;
        private DateTime lastBarTime = DateTime.MinValue;
        private int dayBars;
        private int dayInvalid;
        private int dayGaps;
        private int totalComplete;
        private int totalPartial;
        private int totalInvalid;
        private int totalGaps;
        private bool invalidSetup;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "NQNativeM1DataAuditV1";
                Description = "No-order native NQ 1m Last RTH historical source audit, IST only.";
                Calculate = Calculate.OnBarClose;
                BarsRequiredToTrade = 0;
                OrderFillResolution = OrderFillResolution.Standard;
                IsFillLimitOnTouch = false;
                IncludeCommission = true;
                Slippage = 2;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsInstantiatedOnEachOptimizationIteration = true;
            }
            else if (State == State.Terminated && activeDay != DateTime.MinValue)
            {
                FinishDay();
                Print("NQ_NATIVE_M1_AUDIT_SUMMARY"
                    + " full390=" + totalComplete
                    + " partial=" + totalPartial
                    + " invalidOhlcOrGrid=" + totalInvalid
                    + " missingMinuteGaps=" + totalGaps);
            }
        }

        private static bool OnTickGrid(double price, double tick)
        {
            return price > 0 && Math.Abs(price / tick - Math.Round(price / tick)) < 0.00001;
        }

        private void FinishDay()
        {
            // This audit only includes session bars whose Eastern close
            // labels are between 09:31 and 16:00. Do not infer "data missing"
            // when the configured Trading Hours template intentionally ends
            // early; report the day for manual review instead.
            bool complete = dayBars == 390 && dayInvalid == 0 && dayGaps == 0;
            if (complete)
                totalComplete++;
            else
                totalPartial++;
            totalInvalid += dayInvalid;
            totalGaps += dayGaps;
            Print("NQ_NATIVE_M1_AUDIT_SESSION"
                + " date=" + activeDay.ToString("yyyy-MM-dd")
                + " bars=" + dayBars
                + " invalid=" + dayInvalid
                + " gaps=" + dayGaps
                + " status=" + (complete ? "COMPLETE" : "REVIEW"));
        }

        protected override void OnBarUpdate()
        {
            if (State != State.Historical || BarsInProgress != 0 || invalidSetup)
                return;
            if (BarsPeriod.BarsPeriodType != BarsPeriodType.Minute
                || BarsPeriod.Value != 1
                || Instrument.MasterInstrument.Name != "NQ")
            {
                invalidSetup = true;
                Print("NQ_NATIVE_M1_AUDIT_ABORT: use NQ 1 Minute series only");
                SetState(State.Terminated);
                return;
            }

            // Historical data from 2023 onward is NOT admissible in discovery.
            // Do not accidentally process reserved ISV1/ISV2 or sealed years.
            DateTime stamp = Time[0];
            if (stamp.Year < 2020 || stamp.Year > 2022)
            {
                invalidSetup = true;
                Print("NQ_NATIVE_M1_AUDIT_ABORT: reserved year or unexpected year "
                    + stamp.Year);
                SetState(State.Terminated);
                return;
            }

            int hhmmss = ToTime(stamp); // Requires NinjaTrader display time = ET
            if (hhmmss < 93100 || hhmmss > 160000)
                return;

            if (stamp.Date != activeDay)
            {
                if (activeDay != DateTime.MinValue)
                    FinishDay();
                activeDay = stamp.Date;
                dayBars = 0;
                dayInvalid = 0;
                dayGaps = 0;
                lastBarTime = DateTime.MinValue;
            }

            dayBars++;
            double o = Open[0], h = High[0], l = Low[0], c = Close[0];
            bool invalid = h < Math.Max(o, c) || l > Math.Min(o, c)
                || l > h || !OnTickGrid(o, TickSize)
                || !OnTickGrid(h, TickSize) || !OnTickGrid(l, TickSize)
                || !OnTickGrid(c, TickSize) || Volume[0] < 0;
            if (invalid)
                dayInvalid++;

            if (lastBarTime != DateTime.MinValue
                && (stamp - lastBarTime).TotalMinutes != 1)
                dayGaps++;
            lastBarTime = stamp;
        }
    }
}
