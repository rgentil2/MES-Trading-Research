#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// PDC Small-Gap parity implementation for MES.
    ///
    /// Research specification:
    /// - 1 MES
    /// - complete RTH sessions only (09:30-16:00 ET; NinjaTrader EOB bars 09:31..16:00)
    /// - causal prior-session Wilder ATR14
    /// - 0.10 <= abs(RTH open - PDC) / ATR14_prev < 0.20
    /// - PDC untouched during first five RTH minutes
    /// - fifth-minute close must progress toward PDC
    /// - market entry on next bar open
    /// - SL = 0.30 ATR14_prev
    /// - TP = PDC
    /// - forced time exit at 11:30 ET
    /// - optional frozen USD High/Medium news blackout file
    /// - optional rollover-session file to match the Python no-back-adjustment methodology
    ///
    /// This is a Stage-2 PARITY strategy, not the final live version.
    /// </summary>
    public class PDCSmallGapParity : Strategy
    {
        private const string LongSignal  = "PDC_LONG";
        private const string ShortSignal = "PDC_SHORT";

        private sealed class NewsWindow
        {
            public DateTime StartEt;
            public DateTime EndEt;
        }

        private readonly Dictionary<DateTime, List<NewsWindow>> newsByDate =
            new Dictionary<DateTime, List<NewsWindow>>();

        private readonly HashSet<DateTime> rolloverSessionDates =
            new HashSet<DateTime>();

        // Stage-2 parity only: dates that were complete 390-bar RTH sessions
        // in the Python research dataset.
        private readonly HashSet<DateTime> pythonEligibleSessionDates =
            new HashSet<DateTime>();

        private readonly List<double> atrSeed = new List<double>();

        private TimeZoneInfo easternTimeZone;
        private TimeZoneInfo applicationTimeZone;

        private bool configurationValid;

        // Completed-session state.
        private bool havePreviousCompleteSession;
        private double previousCompleteClose;

        // Current session state.
        private bool haveCurrentSession;
        private bool currentSessionIsRollover;
        private bool currentSessionStartedAtExpectedTime;
        private bool currentSessionEligibleForParity;
        private DateTime currentSessionDateEt;
        private double currentSessionPrevClose;
        private double currentSessionOpen;
        private double currentSessionHigh;
        private double currentSessionLow;
        private double currentSessionClose;
        private DateTime currentSessionLastBarEt;
        private int sessionBarCount;

        // ATR state: Wilder ATR14 computed only from complete 390-bar RTH sessions.
        private bool atrReady;
        private double atr14;

        // Frozen inputs known before current session opens.
        private double pdcForSession;
        private double atrPrevForSession;

        // First-five-minute state.
        private double first5High;
        private double first5Low;
        private bool tradedThisSession;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "PDCSmallGapParity";
                Description = "MES PDC small-gap Stage-2 parity strategy. 2020-2025 research specification.";
                Calculate = Calculate.OnBarClose;

                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsInstantiatedOnEachOptimizationIteration = true;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Gtc;

                BarsRequiredToTrade = 20;

                GapAtrMin = 0.10;
                GapAtrMax = 0.20;
                StopAtrMultiple = 0.30;
                TimeExitEt = 113000;

                UseNewsFilter = true;
                RequireNewsFile = true;
                NewsCsvPath = string.Empty;

                UseRolloverReset = true;
                RequireRolloverFile = true;
                RolloverCsvPath = string.Empty;

                UsePythonSessionUniverse = true;
                RequireSessionUniverseFile = true;
                SessionUniverseCsvPath = string.Empty;

                StrictParity2020To2025 = true;
                AbortIfEntryFillPastPdc = true;
                DebugPrints = false;
            }
            else if (State == State.DataLoaded)
            {
                configurationValid = true;

                try
                {
                    easternTimeZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");
                    applicationTimeZone = NinjaTrader.Core.Globals.GeneralOptions.TimeZoneInfo;
                }
                catch (Exception ex)
                {
                    configurationValid = false;
                    Print("PDC CONFIG ERROR: unable to initialize time zones. " + ex.Message);
                    return;
                }

                if (BarsPeriod.BarsPeriodType != BarsPeriodType.Minute || BarsPeriod.Value != 1)
                {
                    configurationValid = false;
                    Print("PDC CONFIG ERROR: primary series must be 1-minute bars.");
                }

                if (UseNewsFilter)
                    LoadNewsCsv();

                if (UseRolloverReset)
                    LoadRolloverCsv();

                if (UsePythonSessionUniverse)
                    LoadSessionUniverseCsv();

                Print(string.Format(
                    CultureInfo.InvariantCulture,
                    "PDC parity loaded. App TZ={0}; TradingHours={1}; TradingHours TZ={2}; News windows={3}; rollover sessions={4}; eligible Python sessions={5}",
                    applicationTimeZone == null ? "null" : applicationTimeZone.Id,
                    Bars.TradingHours == null ? "null" : Bars.TradingHours.Name,
                    Bars.TradingHours == null || Bars.TradingHours.TimeZoneInfo == null
                        ? "null"
                        : Bars.TradingHours.TimeZoneInfo.Id,
                    CountNewsWindows(),
                    rolloverSessionDates.Count,
                    pythonEligibleSessionDates.Count));
            }
        }

        protected override void OnBarUpdate()
        {
            if (!configurationValid)
                return;

            DateTime et = ToEastern(Time[0]);

            if (StrictParity2020To2025 && (et.Year < 2020 || et.Year > 2025))
                return;

            if (Bars.IsFirstBarOfSession)
                BeginNewSession(et);

            if (!haveCurrentSession)
                return;

            // NinjaTrader's built-in CME US Index Futures RTH template may extend
            // beyond the 09:30-16:00 ET research window (e.g. to 17:00 ET).
            // Python parity uses exactly the 390 one-minute EOB bars 09:31..16:00 ET,
            // so ignore any template bars outside that research window.
            int etClock = EtClock(et);
            if (etClock < 93100 || etClock > 160000)
                return;

            UpdateCurrentSession(et);

            // Only complete RTH-style sessions beginning with the 09:30-09:31 ET bar are eligible.
            if (!currentSessionStartedAtExpectedTime)
                return;

            // Strict Stage-2 parity uses the same complete-session universe that Python used.
            // This prevents data-vendor differences or known early-close/incomplete days from
            // creating extra trades during the parity check. Do not use this as a live filter.
            if (UsePythonSessionUniverse && !currentSessionEligibleForParity)
                return;

            sessionBarCount++;

            if (sessionBarCount <= 5)
            {
                if (sessionBarCount == 1)
                {
                    first5High = High[0];
                    first5Low = Low[0];
                }
                else
                {
                    first5High = Math.Max(first5High, High[0]);
                    first5Low = Math.Min(first5Low, Low[0]);
                }
            }

            // Existing position management. News flat is checked before the timed exit.
            if (Position.MarketPosition != MarketPosition.Flat)
            {
                if (UseNewsFilter && IsNewsFlatBoundary(et))
                {
                    if (Position.MarketPosition == MarketPosition.Long)
                        ExitLong("PDC_NEWS_EXIT", LongSignal);
                    else if (Position.MarketPosition == MarketPosition.Short)
                        ExitShort("PDC_NEWS_EXIT", ShortSignal);

                    if (DebugPrints)
                        Print("PDC NEWS FLAT submitted at EOB " + et.ToString("yyyy-MM-dd HH:mm:ss"));

                    return;
                }

                if (EtClock(et) >= TimeExitEt)
                {
                    if (Position.MarketPosition == MarketPosition.Long)
                        ExitLong("PDC_TIME_EXIT", LongSignal);
                    else if (Position.MarketPosition == MarketPosition.Short)
                        ExitShort("PDC_TIME_EXIT", ShortSignal);

                    if (DebugPrints)
                        Print("PDC TIME EXIT submitted at EOB " + et.ToString("yyyy-MM-dd HH:mm:ss"));

                    return;
                }
            }

            if (Position.MarketPosition != MarketPosition.Flat)
                return;

            // One trade attempt maximum per complete session.
            if (tradedThisSession)
                return;

            // Research signal is evaluated at the close of the fifth RTH minute:
            // bar label 09:35 ET, with the market order filled at the next bar open.
            if (sessionBarCount != 5 || EtClock(et) != 93500)
                return;

            if (double.IsNaN(pdcForSession) || double.IsNaN(atrPrevForSession) || atrPrevForSession <= 0)
                return;

            double gap = currentSessionOpen - pdcForSession;
            if (Math.Abs(gap) < 1e-12)
                return;

            double gapAtr = Math.Abs(gap) / atrPrevForSession;
            if (gapAtr < GapAtrMin || gapAtr >= GapAtrMax)
                return;

            int direction = gap > 0 ? -1 : 1;

            bool untouched = direction == -1
                ? first5Low > pdcForSession
                : first5High < pdcForSession;

            if (!untouched)
                return;

            bool toward = direction == -1
                ? Close[0] < currentSessionOpen
                : Close[0] > currentSessionOpen;

            if (!toward)
                return;

            // Time[0] is the EOB timestamp and also the actual clock boundary of the next-bar open.
            // Therefore this is the intended entry clock used by Python.
            DateTime intendedEntryEt = et;

            if (UseNewsFilter && IsEntryBlackout(intendedEntryEt))
            {
                if (DebugPrints)
                    Print("PDC entry blocked by news at " + intendedEntryEt.ToString("yyyy-MM-dd HH:mm:ss"));
                return;
            }

            int stopTicks = Math.Max(
                1,
                (int)Math.Ceiling((StopAtrMultiple * atrPrevForSession) / TickSize - 1e-12));

            if (direction == 1)
            {
                SetStopLoss(LongSignal, CalculationMode.Ticks, stopTicks, false);
                SetProfitTarget(LongSignal, CalculationMode.Price, pdcForSession);
                EnterLong(1, LongSignal);
            }
            else
            {
                SetStopLoss(ShortSignal, CalculationMode.Ticks, stopTicks, false);
                SetProfitTarget(ShortSignal, CalculationMode.Price, pdcForSession);
                EnterShort(1, ShortSignal);
            }

            tradedThisSession = true;

            if (DebugPrints)
            {
                Print(string.Format(
                    CultureInfo.InvariantCulture,
                    "PDC SIGNAL {0} {1} open={2:F2} pdc={3:F2} atr={4:F4} gapATR={5:F4} stopTicks={6}",
                    intendedEntryEt.ToString("yyyy-MM-dd HH:mm:ss"),
                    direction == 1 ? "LONG" : "SHORT",
                    currentSessionOpen,
                    pdcForSession,
                    atrPrevForSession,
                    gapAtr,
                    stopTicks));
            }
        }

        protected override void OnExecutionUpdate(
            Execution execution,
            string executionId,
            double price,
            int quantity,
            MarketPosition marketPosition,
            string orderId,
            DateTime time)
        {
            if (execution == null || execution.Order == null)
                return;

            string name = execution.Order.Name ?? string.Empty;

            if (DebugPrints)
            {
                Print(string.Format(
                    CultureInfo.InvariantCulture,
                    "PDC EXEC {0} name={1} price={2:F2} qty={3} position={4}",
                    ToEastern(time).ToString("yyyy-MM-dd HH:mm:ss"),
                    name,
                    price,
                    quantity,
                    marketPosition));
            }

            if (!AbortIfEntryFillPastPdc)
                return;

            // Python skips the trade if the next-bar open has already crossed the PDC.
            // Standard 1-minute Strategy Analyzer cannot know that open before submitting the
            // market order, so this parity build immediately flattens if such a fill occurs.
            // Any occurrence must be reviewed as a known implementation mismatch.
            if (name == LongSignal && !double.IsNaN(pdcForSession) && price >= pdcForSession)
            {
                Print("PDC PARITY WARNING: LONG fill already at/through PDC; immediate flatten requested.");
                ExitLong("PDC_BOUNDARY_INVALID", LongSignal);
            }
            else if (name == ShortSignal && !double.IsNaN(pdcForSession) && price <= pdcForSession)
            {
                Print("PDC PARITY WARNING: SHORT fill already at/through PDC; immediate flatten requested.");
                ExitShort("PDC_BOUNDARY_INVALID", ShortSignal);
            }
        }

        private void BeginNewSession(DateTime firstBarEt)
        {
            FinalizeCurrentSession();

            currentSessionDateEt = firstBarEt.Date;
            currentSessionStartedAtExpectedTime = EtClock(firstBarEt) == 93100;
            currentSessionIsRollover =
                UseRolloverReset && rolloverSessionDates.Contains(currentSessionDateEt);
            currentSessionEligibleForParity =
                !UsePythonSessionUniverse || pythonEligibleSessionDates.Contains(currentSessionDateEt);

            atrPrevForSession = atrReady ? atr14 : double.NaN;
            pdcForSession =
                havePreviousCompleteSession && !currentSessionIsRollover
                    ? previousCompleteClose
                    : double.NaN;

            currentSessionPrevClose =
                havePreviousCompleteSession
                    ? previousCompleteClose
                    : double.NaN;

            currentSessionOpen = Open[0];
            currentSessionHigh = High[0];
            currentSessionLow = Low[0];
            currentSessionClose = Close[0];
            currentSessionLastBarEt = firstBarEt;
            sessionBarCount = 0;
            tradedThisSession = false;
            haveCurrentSession = true;

            if (!currentSessionStartedAtExpectedTime)
            {
                Print("PDC PARITY WARNING: session first bar is not 09:31 ET: "
                      + firstBarEt.ToString("yyyy-MM-dd HH:mm:ss"));
            }

            if (DebugPrints)
            {
                Print(string.Format(
                    CultureInfo.InvariantCulture,
                    "PDC SESSION {0} rollover={1} eligible={2} PDC={3} ATRprev={4}",
                    currentSessionDateEt.ToString("yyyy-MM-dd"),
                    currentSessionIsRollover,
                    currentSessionEligibleForParity,
                    double.IsNaN(pdcForSession) ? "NaN" : pdcForSession.ToString("F2", CultureInfo.InvariantCulture),
                    double.IsNaN(atrPrevForSession) ? "NaN" : atrPrevForSession.ToString("F4", CultureInfo.InvariantCulture)));
            }
        }

        private void UpdateCurrentSession(DateTime et)
        {
            currentSessionHigh = Math.Max(currentSessionHigh, High[0]);
            currentSessionLow = Math.Min(currentSessionLow, Low[0]);
            currentSessionClose = Close[0];
            currentSessionLastBarEt = et;
        }

        private void FinalizeCurrentSession()
        {
            if (!haveCurrentSession)
                return;

            // Python prepare_rth() only keeps exactly 390 bars, 09:31..16:00 EOB.
            bool complete =
                currentSessionStartedAtExpectedTime
                && currentSessionEligibleForParity
                && sessionBarCount == 390
                && EtClock(currentSessionLastBarEt) == 160000;

            if (!complete)
            {
                if (DebugPrints)
                {
                    Print(string.Format(
                        CultureInfo.InvariantCulture,
                        "PDC SESSION SKIPPED incomplete {0} bars={1} last={2}",
                        currentSessionDateEt.ToString("yyyy-MM-dd"),
                        sessionBarCount,
                        currentSessionLastBarEt.ToString("HH:mm:ss")));
                }
                return;
            }

            double tr = currentSessionHigh - currentSessionLow;

            // Match Python: on the first complete RTH session of a new contract,
            // do not include the prior-contract close gap in True Range.
            if (!currentSessionIsRollover && !double.IsNaN(currentSessionPrevClose))
            {
                tr = Math.Max(
                    tr,
                    Math.Max(
                        Math.Abs(currentSessionHigh - currentSessionPrevClose),
                        Math.Abs(currentSessionLow - currentSessionPrevClose)));
            }

            UpdateWilderAtr(tr);

            previousCompleteClose = currentSessionClose;
            havePreviousCompleteSession = true;
        }

        private void UpdateWilderAtr(double tr)
        {
            if (!atrReady)
            {
                atrSeed.Add(tr);

                if (atrSeed.Count == 14)
                {
                    double sum = 0;
                    for (int i = 0; i < atrSeed.Count; i++)
                        sum += atrSeed[i];

                    atr14 = sum / 14.0;
                    atrReady = true;
                }

                return;
            }

            atr14 = ((atr14 * 13.0) + tr) / 14.0;
        }

        private DateTime ToEastern(DateTime applicationTime)
        {
            DateTime unspecified = DateTime.SpecifyKind(applicationTime, DateTimeKind.Unspecified);
            return TimeZoneInfo.ConvertTime(unspecified, applicationTimeZone, easternTimeZone);
        }

        private int EtClock(DateTime et)
        {
            return et.Hour * 10000 + et.Minute * 100 + et.Second;
        }

        private bool IsEntryBlackout(DateTime entryEt)
        {
            List<NewsWindow> windows;
            if (!newsByDate.TryGetValue(entryEt.Date, out windows))
                return false;

            for (int i = 0; i < windows.Count; i++)
            {
                if (entryEt >= windows[i].StartEt && entryEt <= windows[i].EndEt)
                    return true;
            }

            return false;
        }

        private bool IsNewsFlatBoundary(DateTime currentBarCloseEt)
        {
            List<NewsWindow> windows;
            if (!newsByDate.TryGetValue(currentBarCloseEt.Date, out windows))
                return false;

            for (int i = 0; i < windows.Count; i++)
            {
                if (currentBarCloseEt == windows[i].StartEt)
                    return true;
            }

            return false;
        }

        private int CountNewsWindows()
        {
            int count = 0;
            foreach (KeyValuePair<DateTime, List<NewsWindow>> kv in newsByDate)
                count += kv.Value.Count;
            return count;
        }

        private void LoadNewsCsv()
        {
            newsByDate.Clear();

            if (string.IsNullOrWhiteSpace(NewsCsvPath) || !File.Exists(NewsCsvPath))
            {
                string msg = "PDC NEWS FILE missing: " + (NewsCsvPath ?? string.Empty);
                Print(msg);
                if (RequireNewsFile)
                    configurationValid = false;
                return;
            }

            try
            {
                using (StreamReader reader = new StreamReader(NewsCsvPath))
                {
                    string header = reader.ReadLine();
                    string line;

                    while ((line = reader.ReadLine()) != null)
                    {
                        if (string.IsNullOrWhiteSpace(line))
                            continue;

                        string[] parts = line.Split(',');
                        if (parts.Length < 2)
                            continue;

                        DateTime startEt;
                        DateTime endEt;

                        if (!DateTime.TryParseExact(
                                parts[0].Trim(),
                                "yyyy-MM-dd HH:mm:ss",
                                CultureInfo.InvariantCulture,
                                DateTimeStyles.None,
                                out startEt))
                            continue;

                        if (!DateTime.TryParseExact(
                                parts[1].Trim(),
                                "yyyy-MM-dd HH:mm:ss",
                                CultureInfo.InvariantCulture,
                                DateTimeStyles.None,
                                out endEt))
                            continue;

                        DateTime key = startEt.Date;
                        List<NewsWindow> windows;
                        if (!newsByDate.TryGetValue(key, out windows))
                        {
                            windows = new List<NewsWindow>();
                            newsByDate[key] = windows;
                        }

                        windows.Add(new NewsWindow { StartEt = startEt, EndEt = endEt });
                    }
                }

                foreach (KeyValuePair<DateTime, List<NewsWindow>> kv in newsByDate)
                    kv.Value.Sort((a, b) => a.StartEt.CompareTo(b.StartEt));
            }
            catch (Exception ex)
            {
                Print("PDC NEWS FILE error: " + ex.Message);
                if (RequireNewsFile)
                    configurationValid = false;
            }
        }

        private void LoadSessionUniverseCsv()
        {
            pythonEligibleSessionDates.Clear();

            if (string.IsNullOrWhiteSpace(SessionUniverseCsvPath) || !File.Exists(SessionUniverseCsvPath))
            {
                string msg = "PDC SESSION UNIVERSE FILE missing: " + (SessionUniverseCsvPath ?? string.Empty);
                Print(msg);
                if (RequireSessionUniverseFile)
                    configurationValid = false;
                return;
            }

            try
            {
                using (StreamReader reader = new StreamReader(SessionUniverseCsvPath))
                {
                    string header = reader.ReadLine();
                    string line;

                    while ((line = reader.ReadLine()) != null)
                    {
                        if (string.IsNullOrWhiteSpace(line))
                            continue;

                        string[] parts = line.Split(',');
                        DateTime d;

                        if (DateTime.TryParseExact(
                                parts[0].Trim(),
                                "yyyy-MM-dd",
                                CultureInfo.InvariantCulture,
                                DateTimeStyles.None,
                                out d))
                        {
                            pythonEligibleSessionDates.Add(d.Date);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Print("PDC SESSION UNIVERSE FILE error: " + ex.Message);
                if (RequireSessionUniverseFile)
                    configurationValid = false;
            }
        }

        private void LoadRolloverCsv()
        {
            rolloverSessionDates.Clear();

            if (string.IsNullOrWhiteSpace(RolloverCsvPath) || !File.Exists(RolloverCsvPath))
            {
                string msg = "PDC ROLLOVER FILE missing: " + (RolloverCsvPath ?? string.Empty);
                Print(msg);
                if (RequireRolloverFile)
                    configurationValid = false;
                return;
            }

            try
            {
                using (StreamReader reader = new StreamReader(RolloverCsvPath))
                {
                    string header = reader.ReadLine();
                    string line;

                    while ((line = reader.ReadLine()) != null)
                    {
                        if (string.IsNullOrWhiteSpace(line))
                            continue;

                        string[] parts = line.Split(',');
                        DateTime d;

                        if (DateTime.TryParseExact(
                                parts[0].Trim(),
                                "yyyy-MM-dd",
                                CultureInfo.InvariantCulture,
                                DateTimeStyles.None,
                                out d))
                        {
                            rolloverSessionDates.Add(d.Date);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Print("PDC ROLLOVER FILE error: " + ex.Message);
                if (RequireRolloverFile)
                    configurationValid = false;
            }
        }

        #region Properties

        [NinjaScriptProperty]
        [Range(0.01, 1.00)]
        [Display(Name = "Gap ATR min", Order = 1, GroupName = "Frozen PDC parameters")]
        public double GapAtrMin { get; set; }

        [NinjaScriptProperty]
        [Range(0.01, 1.00)]
        [Display(Name = "Gap ATR max", Order = 2, GroupName = "Frozen PDC parameters")]
        public double GapAtrMax { get; set; }

        [NinjaScriptProperty]
        [Range(0.01, 2.00)]
        [Display(Name = "Stop ATR multiple", Order = 3, GroupName = "Frozen PDC parameters")]
        public double StopAtrMultiple { get; set; }

        [NinjaScriptProperty]
        [Range(0, 235959)]
        [Display(Name = "Time exit ET (HHmmss)", Order = 4, GroupName = "Frozen PDC parameters")]
        public int TimeExitEt { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Use news filter", Order = 1, GroupName = "Parity files")]
        public bool UseNewsFilter { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Require news file", Order = 2, GroupName = "Parity files")]
        public bool RequireNewsFile { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "News CSV path", Order = 3, GroupName = "Parity files")]
        public string NewsCsvPath { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Use rollover reset", Order = 4, GroupName = "Parity files")]
        public bool UseRolloverReset { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Require rollover file", Order = 5, GroupName = "Parity files")]
        public bool RequireRolloverFile { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Rollover CSV path", Order = 6, GroupName = "Parity files")]
        public string RolloverCsvPath { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Use Python session universe", Order = 7, GroupName = "Parity files")]
        public bool UsePythonSessionUniverse { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Require session universe file", Order = 8, GroupName = "Parity files")]
        public bool RequireSessionUniverseFile { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Session universe CSV path", Order = 9, GroupName = "Parity files")]
        public string SessionUniverseCsvPath { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Strict parity 2020-2025", Order = 1, GroupName = "Safety")]
        public bool StrictParity2020To2025 { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Abort fill past PDC", Order = 2, GroupName = "Safety")]
        public bool AbortIfEntryFillPastPdc { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Debug prints", Order = 3, GroupName = "Safety")]
        public bool DebugPrints { get; set; }

        #endregion
    }
}
