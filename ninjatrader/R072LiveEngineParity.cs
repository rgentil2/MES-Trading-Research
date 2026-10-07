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
    /// R072 live-engine parity candidate.
    ///
    /// Generates R072 signals from:
    /// - causal prior-60 same-block q20/q80 15m range state
    /// - H017 low-volatility override
    /// - wick failure threshold 0.50
    /// - first valid signal/session, cutoff 11:00 ET
    ///
    /// In strict parity mode a Python H017 reference can be used to isolate the
    /// dynamic-block port from minute-history/data-vendor differences. Turning
    /// that reference OFF makes H017 fully computed inside NinjaScript.
    ///
    /// 2026 remains forbidden while StrictParity2020To2025=true.
    /// </summary>
    public class R072LiveEngineParity : Strategy
    {
        private const string LongSignal="R072_LIVE_LONG";
        private const string ShortSignal="R072_LIVE_SHORT";
        private const int RefN=60;

        private sealed class NewsWindow
        {
            public DateTime StartEt;
            public DateTime EndEt;
        }

        private readonly Dictionary<DateTime,List<NewsWindow>> newsByDate=
            new Dictionary<DateTime,List<NewsWindow>>();
        private readonly HashSet<DateTime> pythonEligibleSessionDates=
            new HashSet<DateTime>();
        private readonly HashSet<DateTime> rolloverSessionDates=
            new HashSet<DateTime>();
        private readonly Dictionary<DateTime,DateTime> pythonH017ByDate=
            new Dictionary<DateTime,DateTime>();

        // Prior COMPLETE eligible-session block history. Today's values are added
        // only after the session is finalized.
        private readonly Dictionary<int,List<double>> blockRangeHistory=
            new Dictionary<int,List<double>>();
        private readonly Dictionary<int,double> currentBlockRanges=
            new Dictionary<int,double>();

        // Fully-computed H017 minute history for live mode.
        private readonly Dictionary<int,List<double>> rv30HistoryByMinute=
            new Dictionary<int,List<double>>();
        private readonly Queue<double> last30Returns=new Queue<double>();

        // ATR risk layer.
        private readonly List<double> atrSeed=new List<double>();
        private bool atrReady;
        private double atr14;
        private double atrPrevForSession;
        private bool havePreviousCompleteClose;
        private double previousCompleteClose;

        private TimeZoneInfo easternTimeZone;
        private TimeZoneInfo applicationTimeZone;
        private bool configurationValid;

        private bool haveCurrentSession;
        private bool currentSessionStartedExpected;
        private bool currentSessionEligible;
        private bool currentSessionIsRollover;
        private DateTime currentSessionDateEt;
        private DateTime currentSessionLastBarEt;
        private int sessionBarCount;

        private double currentSessionHigh;
        private double currentSessionLow;
        private double currentSessionClose;
        private double currentSessionPrevClose;

        // Current 15-minute block OHLC.
        private int currentBlockId=-1;
        private double blockOpen;
        private double blockHigh;
        private double blockLow;
        private double blockClose;

        // H017/session signal state.
        private DateTime h017TimeForSession=DateTime.MinValue;
        private DateTime computedH017Time=DateTime.MinValue;
        private DateTime lastResearchBarEt=DateTime.MinValue;
        private double lastResearchClose=double.NaN;
        private bool firstCandidateConsumed;
        private DateTime activeSignalEt=DateTime.MinValue;

        protected override void OnStateChange()
        {
            if(State==State.SetDefaults)
            {
                Name="R072LiveEngineParity";
                Description="R072 causal dynamic HIGH + H017 + wick-failure NinjaScript parity candidate.";
                Calculate=Calculate.OnBarClose;
                EntriesPerDirection=1;
                EntryHandling=EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy=true;
                ExitOnSessionCloseSeconds=30;
                StartBehavior=StartBehavior.WaitUntilFlat;
                TimeInForce=TimeInForce.Gtc;
                BarsRequiredToTrade=20;

                WickThreshold=0.50;
                SignalCutoffEt=110000;
                TimeExitMinutes=30;

                UseNewsFilter=true;
                RequireNewsFile=true;
                NewsCsvPath=string.Empty;

                UsePythonSessionUniverse=true;
                RequireSessionUniverseFile=true;
                SessionUniverseCsvPath=string.Empty;

                UseRolloverReset=true;
                RequireRolloverFile=true;
                RolloverCsvPath=string.Empty;

                UsePythonH017Reference=true;
                RequireH017ReferenceFile=true;
                H017ReferenceCsvPath=string.Empty;

                UseCatastropheStop=false;
                CatastropheStopAtr=0.70;

                StrictParity2020To2025=true;
                WriteEngineAuditCsv=false;
                EngineAuditCsvPath=string.Empty;
                DebugPrints=false;
            }
            else if(State==State.DataLoaded)
            {
                configurationValid=true;
                try
                {
                    easternTimeZone=TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");
                    applicationTimeZone=NinjaTrader.Core.Globals.GeneralOptions.TimeZoneInfo;
                }
                catch(Exception ex)
                {
                    configurationValid=false;
                    Print("R072 LIVE CONFIG ERROR timezone: "+ex.Message);
                    return;
                }

                if(BarsPeriod.BarsPeriodType!=BarsPeriodType.Minute || BarsPeriod.Value!=1)
                {
                    configurationValid=false;
                    Print("R072 LIVE CONFIG ERROR: primary series must be 1-minute.");
                }

                for(int i=0;i<=6;i++)
                    blockRangeHistory[i]=new List<double>();

                if(UseNewsFilter) LoadNewsCsv();
                if(UsePythonSessionUniverse) LoadSessionUniverseCsv();
                if(UseRolloverReset) LoadRolloverCsv();
                if(UsePythonH017Reference) LoadH017ReferenceCsv();

                if(WriteEngineAuditCsv)
                    InitializeAuditCsv();

                Print(string.Format(CultureInfo.InvariantCulture,
                    "R072 live engine loaded. App TZ={0}; TradingHours={1}; News={2}; eligible sessions={3}; rollovers={4}; H017 refs={5}",
                    applicationTimeZone==null?"null":applicationTimeZone.Id,
                    Bars.TradingHours==null?"null":Bars.TradingHours.Name,
                    CountNewsWindows(),pythonEligibleSessionDates.Count,
                    rolloverSessionDates.Count,pythonH017ByDate.Count));
            }
        }

        protected override void OnBarUpdate()
        {
            if(!configurationValid) return;

            DateTime et=ToEastern(Time[0]);
            if(StrictParity2020To2025 && (et.Year<2020 || et.Year>2025))
                return;

            if(Bars.IsFirstBarOfSession)
                BeginNewSession(et);

            if(!haveCurrentSession)
                return;

            int clock=EtClock(et);
            if(clock<93100 || clock>160000)
                return;

            // Fully-computed H017 history intentionally observes every locally
            // available RTH session, matching the Python minute-history concept.
            UpdateComputedH017(et);

            if(!currentSessionStartedExpected)
                return;

            if(UsePythonSessionUniverse && !currentSessionEligible)
                return;

            sessionBarCount++;
            currentSessionLastBarEt=et;
            currentSessionHigh=Math.Max(currentSessionHigh,High[0]);
            currentSessionLow=Math.Min(currentSessionLow,Low[0]);
            currentSessionClose=Close[0];

            int barIndex=sessionBarCount-1;
            int blockId=barIndex/15;
            int within=barIndex%15;

            if(blockId<=6)
            {
                if(within==0)
                {
                    currentBlockId=blockId;
                    blockOpen=Open[0];
                    blockHigh=High[0];
                    blockLow=Low[0];
                    blockClose=Close[0];
                }
                else if(currentBlockId==blockId)
                {
                    blockHigh=Math.Max(blockHigh,High[0]);
                    blockLow=Math.Min(blockLow,Low[0]);
                    blockClose=Close[0];
                }

                if(within==14 && currentBlockId==blockId)
                    EvaluateCompletedBlock(et,blockId);
            }

            ManageOpenPosition(et);
        }

        private void EvaluateCompletedBlock(DateTime et,int blockId)
        {
            double range=blockHigh-blockLow;
            if(range<=0 || blockClose<=0)
                return;

            double rangeBps=range/blockClose*10000.0;
            currentBlockRanges[blockId]=rangeBps;

            List<double> hist=blockRangeHistory[blockId];
            string rawState="UNKNOWN";
            double q20=double.NaN;
            double q80=double.NaN;

            if(hist.Count>=RefN)
            {
                q20=QuantileLast(hist,RefN,0.20);
                q80=QuantileLast(hist,RefN,0.80);

                if(rangeBps<=q20)
                    rawState="LOW";
                else if(rangeBps>=q80)
                    rawState="HIGH";
                else
                    rawState="NORMAL";
            }

            DateTime h017=UsePythonH017Reference
                ? h017TimeForSession
                : computedH017Time;

            bool h017Active=
                h017!=DateTime.MinValue
                && et>=h017
                && et<=h017.AddMinutes(30);

            string engineState=h017Active?"LOW":rawState;

            double upper=(blockHigh-Math.Max(blockOpen,blockClose))/range;
            double lower=(Math.Min(blockOpen,blockClose)-blockLow)/range;
            int direction=0;

            if(engineState=="HIGH" && EtClock(et)<=SignalCutoffEt)
            {
                if(upper>=WickThreshold && blockClose<blockOpen)
                    direction=1;
                else if(lower>=WickThreshold && blockClose>blockOpen)
                    direction=-1;
            }

            AppendEngineAudit(
                et,blockId,rangeBps,q20,q80,rawState,engineState,
                upper,lower,direction,h017);

            if(DebugPrints)
            {
                Print(string.Format(CultureInfo.InvariantCulture,
                    "R072 BLOCK {0} id={1} rngbps={2:F4} q20={3} q80={4} raw={5} engine={6} upper={7:F4} lower={8:F4} dir={9} h017={10}",
                    et.ToString("yyyy-MM-dd HH:mm:ss"),blockId,rangeBps,
                    double.IsNaN(q20)?"NaN":q20.ToString("F4",CultureInfo.InvariantCulture),
                    double.IsNaN(q80)?"NaN":q80.ToString("F4",CultureInfo.InvariantCulture),
                    rawState,engineState,upper,lower,direction,
                    h017==DateTime.MinValue?"NONE":h017.ToString("HH:mm:ss")));
            }

            if(direction==0 || firstCandidateConsumed)
                return;

            // Python selects first R072 candidate/session BEFORE applying news.
            firstCandidateConsumed=true;

            if(UseNewsFilter && IsEntryBlackout(et))
            {
                if(DebugPrints)
                    Print("R072 LIVE first candidate blocked by news "+et.ToString("yyyy-MM-dd HH:mm:ss"));
                return;
            }

            if(UseCatastropheStop)
            {
                if(double.IsNaN(atrPrevForSession) || atrPrevForSession<=0)
                {
                    if(DebugPrints) Print("R072 LIVE skipped: ATR unavailable.");
                    return;
                }

                int stopTicks=Math.Max(1,(int)Math.Ceiling(
                    (CatastropheStopAtr*atrPrevForSession)/TickSize-1e-12));

                if(direction==1)
                    SetStopLoss(LongSignal,CalculationMode.Ticks,stopTicks,false);
                else
                    SetStopLoss(ShortSignal,CalculationMode.Ticks,stopTicks,false);
            }

            activeSignalEt=et;
            if(direction==1)
                EnterLong(1,LongSignal);
            else
                EnterShort(1,ShortSignal);
        }

        private void ManageOpenPosition(DateTime et)
        {
            if(Position.MarketPosition==MarketPosition.Flat)
                return;

            if(UseNewsFilter && IsNewsFlatBoundary(et))
            {
                if(Position.MarketPosition==MarketPosition.Long)
                    ExitLong("R072_NEWS_EXIT",LongSignal);
                else
                    ExitShort("R072_NEWS_EXIT",ShortSignal);
                return;
            }

            if(activeSignalEt!=DateTime.MinValue && et>=activeSignalEt.AddMinutes(TimeExitMinutes))
            {
                if(Position.MarketPosition==MarketPosition.Long)
                    ExitLong("R072_TIME_EXIT",LongSignal);
                else
                    ExitShort("R072_TIME_EXIT",ShortSignal);
            }
        }

        private void BeginNewSession(DateTime firstBarEt)
        {
            FinalizeCurrentSession();

            currentSessionDateEt=firstBarEt.Date;
            currentSessionStartedExpected=EtClock(firstBarEt)==93100;
            currentSessionEligible=
                !UsePythonSessionUniverse || pythonEligibleSessionDates.Contains(currentSessionDateEt);
            currentSessionIsRollover=
                UseRolloverReset && rolloverSessionDates.Contains(currentSessionDateEt);

            atrPrevForSession=atrReady?atr14:double.NaN;
            currentSessionPrevClose=havePreviousCompleteClose?previousCompleteClose:double.NaN;

            currentSessionHigh=High[0];
            currentSessionLow=Low[0];
            currentSessionClose=Close[0];
            currentSessionLastBarEt=firstBarEt;
            sessionBarCount=0;
            currentBlockRanges.Clear();
            currentBlockId=-1;
            firstCandidateConsumed=false;
            activeSignalEt=DateTime.MinValue;
            last30Returns.Clear();
            lastResearchBarEt=DateTime.MinValue;
            lastResearchClose=double.NaN;
            computedH017Time=DateTime.MinValue;

            DateTime refTime;
            h017TimeForSession=
                UsePythonH017Reference && pythonH017ByDate.TryGetValue(currentSessionDateEt,out refTime)
                ? refTime
                : DateTime.MinValue;

            haveCurrentSession=true;
        }

        private void FinalizeCurrentSession()
        {
            if(!haveCurrentSession) return;

            bool complete=
                currentSessionStartedExpected
                && currentSessionEligible
                && sessionBarCount==390
                && EtClock(currentSessionLastBarEt)==160000;

            if(!complete)
                return;

            // Only now add today's block ranges to the historical state windows.
            for(int id=0;id<=6;id++)
            {
                double v;
                if(currentBlockRanges.TryGetValue(id,out v))
                    blockRangeHistory[id].Add(v);
            }

            double tr=currentSessionHigh-currentSessionLow;
            if(!currentSessionIsRollover && !double.IsNaN(currentSessionPrevClose))
            {
                tr=Math.Max(tr,Math.Max(
                    Math.Abs(currentSessionHigh-currentSessionPrevClose),
                    Math.Abs(currentSessionLow-currentSessionPrevClose)));
            }
            UpdateWilderAtr(tr);

            previousCompleteClose=currentSessionClose;
            havePreviousCompleteClose=true;
        }

        private void UpdateWilderAtr(double tr)
        {
            if(!atrReady)
            {
                atrSeed.Add(tr);
                if(atrSeed.Count==14)
                {
                    double sum=0;
                    for(int i=0;i<atrSeed.Count;i++) sum+=atrSeed[i];
                    atr14=sum/14.0;
                    atrReady=true;
                }
                return;
            }
            atr14=((atr14*13.0)+tr)/14.0;
        }

        private void UpdateComputedH017(DateTime et)
        {
            bool consecutive=
                lastResearchBarEt!=DateTime.MinValue
                && et-lastResearchBarEt==TimeSpan.FromMinutes(1)
                && !double.IsNaN(lastResearchClose)
                && lastResearchClose>0
                && Close[0]>0;

            if(!consecutive && lastResearchBarEt!=DateTime.MinValue)
                last30Returns.Clear();

            if(consecutive)
            {
                double r=Math.Log(Close[0]/lastResearchClose);
                last30Returns.Enqueue(r);
                while(last30Returns.Count>30)
                    last30Returns.Dequeue();

                if(last30Returns.Count==30)
                {
                    double ss=0;
                    foreach(double z in last30Returns) ss+=z*z;
                    double rv30=Math.Sqrt(ss)*10000.0;
                    int minute=et.Hour*60+et.Minute;

                    List<double> hist;
                    if(!rv30HistoryByMinute.TryGetValue(minute,out hist))
                    {
                        hist=new List<double>();
                        rv30HistoryByMinute[minute]=hist;
                    }

                    if(computedH017Time==DateTime.MinValue
                        && minute>=601 && minute<=690
                        && hist.Count>=RefN)
                    {
                        double q10=QuantileLast(hist,RefN,0.10);
                        if(rv30<=q10)
                            computedH017Time=et;
                    }

                    hist.Add(rv30);
                }
            }

            lastResearchBarEt=et;
            lastResearchClose=Close[0];
        }

        private double QuantileLast(List<double> src,int n,double p)
        {
            int start=Math.Max(0,src.Count-n);
            int count=src.Count-start;
            if(count<n) return double.NaN;

            double[] a=new double[count];
            for(int i=0;i<count;i++) a[i]=src[start+i];
            Array.Sort(a);

            double idx=(count-1)*p;
            int lo=(int)Math.Floor(idx);
            int hi=(int)Math.Ceiling(idx);
            if(lo==hi) return a[lo];
            double w=idx-lo;
            return a[lo]*(1.0-w)+a[hi]*w;
        }

        private void InitializeAuditCsv()
        {
            if(string.IsNullOrWhiteSpace(EngineAuditCsvPath))
            {
                configurationValid=false;
                Print("R072 LIVE AUDIT ERROR: EngineAuditCsvPath is blank.");
                return;
            }

            try
            {
                File.WriteAllText(
                    EngineAuditCsvPath,
                    "session_date,block_id,block_end_et,range15_bps,q20,q80,raw_state,engine_state,h017_time,upper_wick_ratio,lower_wick_ratio,candidate_direction\r\n");
            }
            catch(Exception ex)
            {
                configurationValid=false;
                Print("R072 LIVE AUDIT ERROR: "+ex.Message);
            }
        }

        private void AppendEngineAudit(
            DateTime et,int blockId,double rangeBps,double q20,double q80,
            string rawState,string engineState,double upper,double lower,
            int direction,DateTime h017)
        {
            if(!WriteEngineAuditCsv || string.IsNullOrWhiteSpace(EngineAuditCsvPath))
                return;

            try
            {
                string line=string.Join(",",new string[]{
                    currentSessionDateEt.ToString("yyyy-MM-dd"),
                    blockId.ToString(CultureInfo.InvariantCulture),
                    et.ToString("yyyy-MM-dd HH:mm:ss"),
                    rangeBps.ToString("R",CultureInfo.InvariantCulture),
                    double.IsNaN(q20)?"":q20.ToString("R",CultureInfo.InvariantCulture),
                    double.IsNaN(q80)?"":q80.ToString("R",CultureInfo.InvariantCulture),
                    rawState,
                    engineState,
                    h017==DateTime.MinValue?"":h017.ToString("yyyy-MM-dd HH:mm:ss"),
                    upper.ToString("R",CultureInfo.InvariantCulture),
                    lower.ToString("R",CultureInfo.InvariantCulture),
                    direction.ToString(CultureInfo.InvariantCulture)
                });
                File.AppendAllText(EngineAuditCsvPath,line+"\r\n");
            }
            catch(Exception ex)
            {
                Print("R072 LIVE AUDIT WRITE ERROR: "+ex.Message);
            }
        }

        private DateTime ToEastern(DateTime applicationTime)
        {
            DateTime u=DateTime.SpecifyKind(applicationTime,DateTimeKind.Unspecified);
            return TimeZoneInfo.ConvertTime(u,applicationTimeZone,easternTimeZone);
        }

        private int EtClock(DateTime et)
        {
            return et.Hour*10000+et.Minute*100+et.Second;
        }

        private bool IsEntryBlackout(DateTime et)
        {
            List<NewsWindow> w;
            if(!newsByDate.TryGetValue(et.Date,out w)) return false;
            for(int i=0;i<w.Count;i++)
                if(et>=w[i].StartEt && et<=w[i].EndEt) return true;
            return false;
        }

        private bool IsNewsFlatBoundary(DateTime et)
        {
            List<NewsWindow> w;
            if(!newsByDate.TryGetValue(et.Date,out w)) return false;
            for(int i=0;i<w.Count;i++)
                if(et==w[i].StartEt) return true;
            return false;
        }

        private int CountNewsWindows()
        {
            int n=0;
            foreach(KeyValuePair<DateTime,List<NewsWindow>> kv in newsByDate) n+=kv.Value.Count;
            return n;
        }

        private void LoadNewsCsv()
        {
            newsByDate.Clear();
            if(string.IsNullOrWhiteSpace(NewsCsvPath) || !File.Exists(NewsCsvPath))
            {
                Print("R072 LIVE NEWS FILE missing: "+(NewsCsvPath??string.Empty));
                if(RequireNewsFile) configurationValid=false;
                return;
            }
            try
            {
                using(StreamReader reader=new StreamReader(NewsCsvPath))
                {
                    string header=reader.ReadLine();
                    string line;
                    while((line=reader.ReadLine())!=null)
                    {
                        if(string.IsNullOrWhiteSpace(line)) continue;
                        string[] p=line.Split(',');
                        if(p.Length<2) continue;
                        DateTime s,e;
                        if(!DateTime.TryParseExact(p[0].Trim(),"yyyy-MM-dd HH:mm:ss",CultureInfo.InvariantCulture,DateTimeStyles.None,out s)) continue;
                        if(!DateTime.TryParseExact(p[1].Trim(),"yyyy-MM-dd HH:mm:ss",CultureInfo.InvariantCulture,DateTimeStyles.None,out e)) continue;
                        List<NewsWindow> w;
                        if(!newsByDate.TryGetValue(s.Date,out w))
                        {
                            w=new List<NewsWindow>();
                            newsByDate[s.Date]=w;
                        }
                        w.Add(new NewsWindow{StartEt=s,EndEt=e});
                    }
                }
            }
            catch(Exception ex)
            {
                Print("R072 LIVE NEWS FILE error: "+ex.Message);
                if(RequireNewsFile) configurationValid=false;
            }
        }

        private void LoadSessionUniverseCsv()
        {
            pythonEligibleSessionDates.Clear();
            if(string.IsNullOrWhiteSpace(SessionUniverseCsvPath) || !File.Exists(SessionUniverseCsvPath))
            {
                Print("R072 LIVE SESSION FILE missing: "+(SessionUniverseCsvPath??string.Empty));
                if(RequireSessionUniverseFile) configurationValid=false;
                return;
            }
            try
            {
                using(StreamReader reader=new StreamReader(SessionUniverseCsvPath))
                {
                    string header=reader.ReadLine();
                    string line;
                    while((line=reader.ReadLine())!=null)
                    {
                        if(string.IsNullOrWhiteSpace(line)) continue;
                        string[] p=line.Split(',');
                        DateTime d;
                        if(DateTime.TryParseExact(p[0].Trim(),"yyyy-MM-dd",CultureInfo.InvariantCulture,DateTimeStyles.None,out d))
                            pythonEligibleSessionDates.Add(d.Date);
                    }
                }
            }
            catch(Exception ex)
            {
                Print("R072 LIVE SESSION FILE error: "+ex.Message);
                if(RequireSessionUniverseFile) configurationValid=false;
            }
        }

        private void LoadRolloverCsv()
        {
            rolloverSessionDates.Clear();
            if(string.IsNullOrWhiteSpace(RolloverCsvPath) || !File.Exists(RolloverCsvPath))
            {
                Print("R072 LIVE ROLLOVER FILE missing: "+(RolloverCsvPath??string.Empty));
                if(RequireRolloverFile) configurationValid=false;
                return;
            }
            try
            {
                using(StreamReader reader=new StreamReader(RolloverCsvPath))
                {
                    string header=reader.ReadLine();
                    string line;
                    while((line=reader.ReadLine())!=null)
                    {
                        if(string.IsNullOrWhiteSpace(line)) continue;
                        string[] p=line.Split(',');
                        DateTime d;
                        if(DateTime.TryParseExact(p[0].Trim(),"yyyy-MM-dd",CultureInfo.InvariantCulture,DateTimeStyles.None,out d))
                            rolloverSessionDates.Add(d.Date);
                    }
                }
            }
            catch(Exception ex)
            {
                Print("R072 LIVE ROLLOVER FILE error: "+ex.Message);
                if(RequireRolloverFile) configurationValid=false;
            }
        }

        private void LoadH017ReferenceCsv()
        {
            pythonH017ByDate.Clear();
            if(string.IsNullOrWhiteSpace(H017ReferenceCsvPath) || !File.Exists(H017ReferenceCsvPath))
            {
                Print("R072 LIVE H017 REF missing: "+(H017ReferenceCsvPath??string.Empty));
                if(RequireH017ReferenceFile) configurationValid=false;
                return;
            }
            try
            {
                using(StreamReader reader=new StreamReader(H017ReferenceCsvPath))
                {
                    string header=reader.ReadLine();
                    string line;
                    while((line=reader.ReadLine())!=null)
                    {
                        if(string.IsNullOrWhiteSpace(line)) continue;
                        string[] p=line.Split(',');
                        if(p.Length<2) continue;
                        DateTime d,t;
                        if(!DateTime.TryParseExact(p[0].Trim(),"yyyy-MM-dd",CultureInfo.InvariantCulture,DateTimeStyles.None,out d)) continue;
                        if(!DateTime.TryParseExact(p[1].Trim(),"yyyy-MM-dd HH:mm:ss",CultureInfo.InvariantCulture,DateTimeStyles.None,out t)) continue;
                        pythonH017ByDate[d.Date]=t;
                    }
                }
            }
            catch(Exception ex)
            {
                Print("R072 LIVE H017 REF error: "+ex.Message);
                if(RequireH017ReferenceFile) configurationValid=false;
            }
        }

        #region Properties
        [NinjaScriptProperty]
        [Range(0.10,0.90)]
        [Display(Name="Wick threshold",Order=1,GroupName="Frozen R072 parameters")]
        public double WickThreshold{get;set;}

        [NinjaScriptProperty]
        [Range(0,235959)]
        [Display(Name="Signal cutoff ET",Order=2,GroupName="Frozen R072 parameters")]
        public int SignalCutoffEt{get;set;}

        [NinjaScriptProperty]
        [Range(1,120)]
        [Display(Name="Time exit minutes",Order=3,GroupName="Frozen R072 parameters")]
        public int TimeExitMinutes{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Use catastrophe stop",Order=4,GroupName="Frozen R072 parameters")]
        public bool UseCatastropheStop{get;set;}

        [NinjaScriptProperty]
        [Range(0.05,3.00)]
        [Display(Name="Catastrophe stop ATR",Order=5,GroupName="Frozen R072 parameters")]
        public double CatastropheStopAtr{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Use news filter",Order=1,GroupName="Parity files")]
        public bool UseNewsFilter{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Require news file",Order=2,GroupName="Parity files")]
        public bool RequireNewsFile{get;set;}

        [NinjaScriptProperty]
        [Display(Name="News CSV path",Order=3,GroupName="Parity files")]
        public string NewsCsvPath{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Use Python session universe",Order=4,GroupName="Parity files")]
        public bool UsePythonSessionUniverse{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Require session universe file",Order=5,GroupName="Parity files")]
        public bool RequireSessionUniverseFile{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Session universe CSV path",Order=6,GroupName="Parity files")]
        public string SessionUniverseCsvPath{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Use rollover reset",Order=7,GroupName="Parity files")]
        public bool UseRolloverReset{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Require rollover file",Order=8,GroupName="Parity files")]
        public bool RequireRolloverFile{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Rollover CSV path",Order=9,GroupName="Parity files")]
        public string RolloverCsvPath{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Use Python H017 reference",Order=10,GroupName="Parity files")]
        public bool UsePythonH017Reference{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Require H017 reference file",Order=11,GroupName="Parity files")]
        public bool RequireH017ReferenceFile{get;set;}

        [NinjaScriptProperty]
        [Display(Name="H017 reference CSV path",Order=12,GroupName="Parity files")]
        public string H017ReferenceCsvPath{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Strict parity 2020-2025",Order=1,GroupName="Safety")]
        public bool StrictParity2020To2025{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Write engine audit CSV",Order=2,GroupName="Safety")]
        public bool WriteEngineAuditCsv{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Engine audit CSV path",Order=3,GroupName="Safety")]
        public string EngineAuditCsvPath{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Debug prints",Order=4,GroupName="Safety")]
        public bool DebugPrints{get;set;}
        #endregion
    }
}
