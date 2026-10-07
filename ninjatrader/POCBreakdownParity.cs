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
    /// POC Breakdown Stage-2 parity implementation for MES.
    ///
    /// Research specification:
    /// - complete Python-eligible RTH sessions only
    /// - prior-session POC = HLC3 rounded to nearest 0.25, volume summed by price bin
    /// - deterministic equal-volume tie-break = nearest to volume-weighted profile mean
    /// - current RTH open > prior POC
    /// - FIRST bar touching prior POC must close below it
    /// - SHORT at next 1-minute open
    /// - fixed 15-minute exit from contact signal
    /// - frozen USD High/Medium news policy
    ///
    /// This parity build intentionally does NOT yet enable the later 0.45 ATR
    /// catastrophe stop. First prove the 109-trade base implementation.
    /// </summary>
    public class POCBreakdownParity : Strategy
    {
        private const string ShortSignal = "POC_SHORT";
        private const double PocTick = 0.25;

        private sealed class NewsWindow
        {
            public DateTime StartEt;
            public DateTime EndEt;
        }

        private readonly Dictionary<DateTime, List<NewsWindow>> newsByDate =
            new Dictionary<DateTime, List<NewsWindow>>();

        private readonly HashSet<DateTime> rolloverSessionDates =
            new HashSet<DateTime>();

        private readonly HashSet<DateTime> pythonEligibleSessionDates =
            new HashSet<DateTime>();

        private readonly Dictionary<double, double> currentProfile =
            new Dictionary<double, double>();
        private readonly List<double> atrSeed = new List<double>();

        private TimeZoneInfo easternTimeZone;
        private TimeZoneInfo applicationTimeZone;
        private bool configurationValid;

        private bool haveCurrentSession;
        private bool currentSessionStartedAtExpectedTime;
        private bool currentSessionEligibleForParity;
        private bool currentSessionIsRollover;
        private DateTime currentSessionDateEt;
        private DateTime currentSessionLastBarEt;
        private int sessionBarCount;

        private bool havePreviousCompletePoc;
        private double previousCompletePoc;
        private bool havePreviousCompleteClose;
        private double previousCompleteClose;

        // Causal Wilder ATR14 from completed eligible RTH sessions.
        private bool atrReady;
        private double atr14;
        private double atrPrevForSession;

        private double pocForSession;
        private double currentSessionOpen;
        private double currentSessionHigh;
        private double currentSessionLow;
        private double currentSessionClose;
        private double currentSessionPrevClose;

        private bool firstTouchConsumed;
        private bool tradedThisSession;
        private DateTime contactSignalEt;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "POCBreakdownParity";
                Description = "MES POC Breakdown Stage-2 parity strategy. 2020-2025 only.";
                Calculate = Calculate.OnBarClose;

                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsInstantiatedOnEachOptimizationIteration = true;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Gtc;
                BarsRequiredToTrade = 20;

                ContactCutoffEt = 113000;
                TimeExitMinutes = 15;
                UseCatastropheStop = false;
                CatastropheStopAtr = 0.45;

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
                    Print("POC CONFIG ERROR: unable to initialize time zones. " + ex.Message);
                    return;
                }

                if (BarsPeriod.BarsPeriodType != BarsPeriodType.Minute || BarsPeriod.Value != 1)
                {
                    configurationValid = false;
                    Print("POC CONFIG ERROR: primary series must be 1-minute bars.");
                }

                if (UseNewsFilter)
                    LoadNewsCsv();

                if (UseRolloverReset)
                    LoadRolloverCsv();

                if (UsePythonSessionUniverse)
                    LoadSessionUniverseCsv();

                Print(string.Format(
                    CultureInfo.InvariantCulture,
                    "POC parity loaded. App TZ={0}; TradingHours={1}; TradingHours TZ={2}; News windows={3}; rollover sessions={4}; eligible Python sessions={5}",
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

            int clock = EtClock(et);

            // Match Python research window exactly.
            if (clock < 93100 || clock > 160000)
                return;

            if (!currentSessionStartedAtExpectedTime)
                return;

            if (UsePythonSessionUniverse && !currentSessionEligibleForParity)
                return;

            sessionBarCount++;
            currentSessionLastBarEt = et;
            currentSessionHigh = Math.Max(currentSessionHigh, High[0]);
            currentSessionLow = Math.Min(currentSessionLow, Low[0]);
            currentSessionClose = Close[0];
            AddProfileBar();

            // Manage existing SHORT.
            if (Position.MarketPosition == MarketPosition.Short)
            {
                // Match Python collision semantics: if the scheduled H15 exit
                // lands exactly on the T-5 boundary, the timed exit is already
                // due at that boundary. A news-forced exit applies only when the
                // position would otherwise remain open beyond it.
                if (contactSignalEt != DateTime.MinValue
                    && et >= contactSignalEt.AddMinutes(TimeExitMinutes))
                {
                    ExitShort("POC_TIME_EXIT", ShortSignal);
                    if (DebugPrints)
                        Print("POC TIME EXIT submitted at EOB " + et.ToString("yyyy-MM-dd HH:mm:ss"));
                    return;
                }

                if (UseNewsFilter && IsNewsFlatBoundary(et))
                {
                    ExitShort("POC_NEWS_EXIT", ShortSignal);
                    if (DebugPrints)
                        Print("POC NEWS FLAT submitted at EOB " + et.ToString("yyyy-MM-dd HH:mm:ss"));
                    return;
                }
            }

            if (Position.MarketPosition != MarketPosition.Flat)
                return;

            if (tradedThisSession || firstTouchConsumed)
                return;

            if (double.IsNaN(pocForSession))
                return;

            // Historical rule requires current RTH open strictly above prior POC.
            if (!(currentSessionOpen > pocForSession))
                return;

            if (clock > ContactCutoffEt)
                return;

            // First touch only.
            if (Low[0] <= pocForSession)
            {
                firstTouchConsumed = true;

                // First touch must close below POC; otherwise setup is dead for the day.
                if (!(Close[0] < pocForSession))
                {
                    if (DebugPrints)
                        Print("POC first touch failed close-below condition at " + et.ToString("yyyy-MM-dd HH:mm:ss"));
                    return;
                }

                DateTime intendedEntryEt = et;

                if (UseNewsFilter && IsEntryBlackout(intendedEntryEt))
                {
                    if (DebugPrints)
                        Print("POC entry blocked by news at " + intendedEntryEt.ToString("yyyy-MM-dd HH:mm:ss"));
                    return;
                }

                contactSignalEt = et;

                if (UseCatastropheStop)
                {
                    if (double.IsNaN(atrPrevForSession) || atrPrevForSession <= 0)
                        return;

                    int stopTicks = Math.Max(
                        1,
                        (int)Math.Ceiling(
                            (CatastropheStopAtr * atrPrevForSession) / TickSize - 1e-12));
                    SetStopLoss(ShortSignal, CalculationMode.Ticks, stopTicks, false);
                }

                EnterShort(1, ShortSignal);
                tradedThisSession = true;

                if (DebugPrints)
                {
                    Print(string.Format(
                        CultureInfo.InvariantCulture,
                        "POC SIGNAL {0} SHORT open={1:F2} prevPOC={2:F2} contactClose={3:F2}",
                        intendedEntryEt.ToString("yyyy-MM-dd HH:mm:ss"),
                        currentSessionOpen,
                        pocForSession,
                        Close[0]));
                }
            }
        }

        private void BeginNewSession(DateTime firstBarEt)
        {
            FinalizeCurrentSession();

            currentSessionDateEt = firstBarEt.Date;
            currentSessionStartedAtExpectedTime = EtClock(firstBarEt) == 93100;
            currentSessionEligibleForParity =
                !UsePythonSessionUniverse || pythonEligibleSessionDates.Contains(currentSessionDateEt);
            currentSessionIsRollover =
                UseRolloverReset && rolloverSessionDates.Contains(currentSessionDateEt);

            pocForSession =
                havePreviousCompletePoc && !currentSessionIsRollover
                    ? previousCompletePoc
                    : double.NaN;

            atrPrevForSession = atrReady ? atr14 : double.NaN;
            currentSessionPrevClose =
                havePreviousCompleteClose ? previousCompleteClose : double.NaN;

            currentSessionOpen = Open[0];
            currentSessionHigh = High[0];
            currentSessionLow = Low[0];
            currentSessionClose = Close[0];
            currentSessionLastBarEt = firstBarEt;
            sessionBarCount = 0;
            firstTouchConsumed = false;
            tradedThisSession = false;
            contactSignalEt = DateTime.MinValue;
            currentProfile.Clear();
            haveCurrentSession = true;

            if (DebugPrints)
            {
                Print(string.Format(
                    CultureInfo.InvariantCulture,
                    "POC SESSION {0} rollover={1} eligible={2} prevPOC={3}",
                    currentSessionDateEt.ToString("yyyy-MM-dd"),
                    currentSessionIsRollover,
                    currentSessionEligibleForParity,
                    double.IsNaN(pocForSession)
                        ? "NaN"
                        : pocForSession.ToString("F2", CultureInfo.InvariantCulture)));
            }
        }

        private void AddProfileBar()
        {
            double typical = (High[0] + Low[0] + Close[0]) / 3.0;
            double bin = BinTick(typical);
            double vol = Convert.ToDouble(Volume[0]);

            double prior;
            if (currentProfile.TryGetValue(bin, out prior))
                currentProfile[bin] = prior + vol;
            else
                currentProfile[bin] = vol;
        }

        private double BinTick(double x)
        {
            return Math.Round(
                Math.Floor(x / PocTick + 0.5) * PocTick,
                2,
                MidpointRounding.AwayFromZero);
        }

        private double ComputeSessionPoc()
        {
            if (currentProfile.Count == 0)
                return double.NaN;

            double maxVol = double.MinValue;
            double weightedPriceSum = 0.0;
            double totalVol = 0.0;

            foreach (KeyValuePair<double, double> kv in currentProfile)
            {
                if (kv.Value > maxVol)
                    maxVol = kv.Value;

                weightedPriceSum += kv.Key * kv.Value;
                totalVol += kv.Value;
            }

            if (totalVol <= 0)
                return double.NaN;

            double center = weightedPriceSum / totalVol;
            double best = double.NaN;
            double bestDistance = double.MaxValue;

            foreach (KeyValuePair<double, double> kv in currentProfile)
            {
                if (Math.Abs(kv.Value - maxVol) > 1e-9)
                    continue;

                double d = Math.Abs(kv.Key - center);
                if (d < bestDistance - 1e-12)
                {
                    best = kv.Key;
                    bestDistance = d;
                }
                else if (Math.Abs(d - bestDistance) <= 1e-12 && kv.Key < best)
                {
                    // Deterministic fallback matching numpy argmin's first sorted price-bin behavior.
                    best = kv.Key;
                }
            }

            return best;
        }

        private void FinalizeCurrentSession()
        {
            if (!haveCurrentSession)
                return;

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
                        "POC SESSION SKIPPED incomplete/ineligible {0} bars={1} last={2}",
                        currentSessionDateEt.ToString("yyyy-MM-dd"),
                        sessionBarCount,
                        currentSessionLastBarEt.ToString("HH:mm:ss")));
                }
                return;
            }

            double p = ComputeSessionPoc();
            if (!double.IsNaN(p))
            {
                previousCompletePoc = p;
                havePreviousCompletePoc = true;
            }

            double tr = currentSessionHigh - currentSessionLow;
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
            havePreviousCompleteClose = true;

            if (DebugPrints)
            {
                Print(string.Format(
                    CultureInfo.InvariantCulture,
                    "POC FINAL {0} POC={1:F2} ATRclose={2}",
                    currentSessionDateEt.ToString("yyyy-MM-dd"),
                    p,
                    atrReady ? atr14.ToString("F4", CultureInfo.InvariantCulture) : "NaN"));
            }
        }

        private void UpdateWilderAtr(double tr)
        {
            if (!atrReady)
            {
                atrSeed.Add(tr);
                if (atrSeed.Count == 14)
                {
                    double sum = 0.0;
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
                if (entryEt >= windows[i].StartEt && entryEt <= windows[i].EndEt)
                    return true;

            return false;
        }

        private bool IsNewsFlatBoundary(DateTime currentBarCloseEt)
        {
            List<NewsWindow> windows;
            if (!newsByDate.TryGetValue(currentBarCloseEt.Date, out windows))
                return false;

            for (int i = 0; i < windows.Count; i++)
                if (currentBarCloseEt == windows[i].StartEt)
                    return true;

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
                Print("POC NEWS FILE missing: " + (NewsCsvPath ?? string.Empty));
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

                        if (!DateTime.TryParseExact(parts[0].Trim(), "yyyy-MM-dd HH:mm:ss",
                            CultureInfo.InvariantCulture, DateTimeStyles.None, out startEt))
                            continue;

                        if (!DateTime.TryParseExact(parts[1].Trim(), "yyyy-MM-dd HH:mm:ss",
                            CultureInfo.InvariantCulture, DateTimeStyles.None, out endEt))
                            continue;

                        List<NewsWindow> windows;
                        if (!newsByDate.TryGetValue(startEt.Date, out windows))
                        {
                            windows = new List<NewsWindow>();
                            newsByDate[startEt.Date] = windows;
                        }

                        windows.Add(new NewsWindow { StartEt = startEt, EndEt = endEt });
                    }
                }

                foreach (KeyValuePair<DateTime, List<NewsWindow>> kv in newsByDate)
                    kv.Value.Sort((a, b) => a.StartEt.CompareTo(b.StartEt));
            }
            catch (Exception ex)
            {
                Print("POC NEWS FILE error: " + ex.Message);
                if (RequireNewsFile)
                    configurationValid = false;
            }
        }

        private void LoadRolloverCsv()
        {
            rolloverSessionDates.Clear();

            if (string.IsNullOrWhiteSpace(RolloverCsvPath) || !File.Exists(RolloverCsvPath))
            {
                Print("POC ROLLOVER FILE missing: " + (RolloverCsvPath ?? string.Empty));
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

                        if (DateTime.TryParseExact(parts[0].Trim(), "yyyy-MM-dd",
                            CultureInfo.InvariantCulture, DateTimeStyles.None, out d))
                            rolloverSessionDates.Add(d.Date);
                    }
                }
            }
            catch (Exception ex)
            {
                Print("POC ROLLOVER FILE error: " + ex.Message);
                if (RequireRolloverFile)
                    configurationValid = false;
            }
        }

        private void LoadSessionUniverseCsv()
        {
            pythonEligibleSessionDates.Clear();

            if (string.IsNullOrWhiteSpace(SessionUniverseCsvPath) || !File.Exists(SessionUniverseCsvPath))
            {
                Print("POC SESSION UNIVERSE FILE missing: " + (SessionUniverseCsvPath ?? string.Empty));
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

                        if (DateTime.TryParseExact(parts[0].Trim(), "yyyy-MM-dd",
                            CultureInfo.InvariantCulture, DateTimeStyles.None, out d))
                            pythonEligibleSessionDates.Add(d.Date);
                    }
                }
            }
            catch (Exception ex)
            {
                Print("POC SESSION UNIVERSE FILE error: " + ex.Message);
                if (RequireSessionUniverseFile)
                    configurationValid = false;
            }
        }

        #region Properties

        [NinjaScriptProperty]
        [Range(0, 235959)]
        [Display(Name = "Contact cutoff ET (HHmmss)", Order = 1, GroupName = "Frozen POC parameters")]
        public int ContactCutoffEt { get; set; }

        [NinjaScriptProperty]
        [Range(1, 120)]
        [Display(Name = "Time exit minutes", Order = 2, GroupName = "Frozen POC parameters")]
        public int TimeExitMinutes { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Use catastrophe stop", Order = 3, GroupName = "Frozen POC parameters")]
        public bool UseCatastropheStop { get; set; }

        [NinjaScriptProperty]
        [Range(0.05, 3.00)]
        [Display(Name = "Catastrophe stop ATR", Order = 4, GroupName = "Frozen POC parameters")]
        public double CatastropheStopAtr { get; set; }

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
        [Display(Name = "Debug prints", Order = 2, GroupName = "Safety")]
        public bool DebugPrints { get; set; }

        #endregion
    }
}
