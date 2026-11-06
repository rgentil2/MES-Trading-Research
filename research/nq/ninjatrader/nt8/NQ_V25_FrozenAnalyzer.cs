// NINJATRADER 8 ONLY — S0.86 V25 ONE-SHOT VALIDATION STRATEGY.
// Run IN STRATEGY ANALYZER, HISTORICAL only, with the frozen 20
// EXCANv19 genes after an actual V23 3-5 member portfolio has passed.
// DO NOT ENABLE ON LIVE CHART / BROKER. Defaults are DISARMED.
// Pure math dependency list: see tools/nq-v25-native/README.md.
// NT8 uses END-stamped 1-minute bars; subtract exactly one minute to
// recover the V12/V19 completed M1 bar START (New York wall time).
// NT8 native historical fills are not V12's pessimistic fill model.
// Export BOTH bars and native fills to enable explicit comparison.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQ_V25_FrozenAnalyzer : Strategy
    {
        private NQNativeV25FrozenSignalCore core;
        private int[] genes;
        private string entryTag,prefix,canonical;
        private StreamWriter barWriter;
        private DateTime day=DateTime.MinValue;
        private double closedEquity,sessionStartEquity;
        private int dailySubmissions,closedProcessed,exportBars;
        private bool validated;

        [NinjaScriptProperty]
        [Display(Name="Historical validation ARMED (never live)",
            GroupName="V25 Safety",Order=0)]
        public bool ArmHistoricalValidation{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Confirm NT8 timestamps are New York ET",
            GroupName="V25 Safety",Order=1)]
        public bool ConfirmEndStampedET{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Frozen V25 package SHA256",
            GroupName="V25 Frozen Identity",Order=2)]
        public string FrozenV25LockSHA256{get;set;}

        [NinjaScriptProperty]
        [Display(Name="EXCANv19 canonical Base64",
            GroupName="V25 Frozen Identity",Order=3)]
        public string FrozenCanonicalBase64{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Frozen 20-gene vector separated by /",
            GroupName="V25 Frozen Identity",Order=4)]
        public string FrozenGenes20{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Approved V23 candidate ID",
            GroupName="V25 Frozen Identity",Order=5)]
        public string CandidateId{get;set;}

        [NinjaScriptProperty]
        [Display(Name="DEV or EXTERNAL or FINAL; no automatic OOS unlock",
            GroupName="V25 Historical Scope",Order=6)]
        public string HistoricalScope{get;set;}

        [NinjaScriptProperty]
        [Display(Name="Empty folder for one-shot exported reports",
            GroupName="V25 Audit Output",Order=7)]
        public string ReportDirectory{get;set;}

        protected override void OnStateChange()
        {
            if(State==State.SetDefaults)
            {
                Name="NQ_V25_FrozenAnalyzer";
                Description="V25 historical-only frozen EXCANv19 NT8 fill parity, research only";
                Calculate=Calculate.OnBarClose;
                EntriesPerDirection=1;
                EntryHandling=EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy=false;
                IsInstantiatedOnEachOptimizationIteration=true;
                BarsRequiredToTrade=0;
                Slippage=2;
                StartBehavior=StartBehavior.WaitUntilFlat;
                ArmHistoricalValidation=false;
                ConfirmEndStampedET=false;
                FrozenV25LockSHA256="";
                FrozenCanonicalBase64="";
                FrozenGenes20="";
                CandidateId="";
                HistoricalScope="DEV";
                ReportDirectory="";
            }
            else if(State==State.Configure)
            {
                // NT8 disables historical Trade objects by default
                // in Strategy Analyzer. V25 needs exact native
                // trade receipts for bar-by-bar comparison.
                IncludeTradeHistoryInBacktest=true;
            }
            else if(State==State.DataLoaded)
            {
                if(!ArmHistoricalValidation)return;
                if(!ConfirmEndStampedET)
                    throw new InvalidOperationException(
                        "V25_SET_PLATFORM_TIMESTAMPS_TO_NEW_YORK_ET_AND_CONFIRM");
                if(BarsPeriod.BarsPeriodType!=BarsPeriodType.Minute||
                   BarsPeriod.Value!=1)
                    throw new InvalidOperationException(
                        "V25_REQUIRES_PRIMARY_ONE_MINUTE_LAST_BARS");
                string full=Instrument.FullName.ToUpperInvariant();
                if(!full.StartsWith("NQ ")||
                   !(full.Contains("12-26")||
                     full.Contains("DEC2026")||
                     full.Contains("12-2026")))
                    throw new InvalidOperationException(
                        "V25_INSTRUMENT_MUST_BE_NQ_DEC2026");
                if(FrozenV25LockSHA256==null||
                   FrozenV25LockSHA256.Length!=64||
                   String.IsNullOrWhiteSpace(FrozenCanonicalBase64)||
                   String.IsNullOrWhiteSpace(FrozenGenes20)||
                   String.IsNullOrWhiteSpace(CandidateId)||
                   CandidateId.Any(x=>!Char.IsLetterOrDigit(x)&&
                     x!='_'&&x!='-')||
                   (HistoricalScope!="DEV"&&HistoricalScope!="EXTERNAL"&&
                    HistoricalScope!="FINAL")||
                   String.IsNullOrWhiteSpace(ReportDirectory)||
                   !Path.IsPathRooted(ReportDirectory))
                    throw new InvalidOperationException(
                        "V25_APPROVED_LOCK_CANONICAL_GENES_SCOPE_OUTPUT_REQUIRED");
                try
                {
                    genes=FrozenGenes20.Split('/').Select(x=>
                        Int32.Parse(x,CultureInfo.InvariantCulture)).ToArray();
                    canonical=Encoding.UTF8.GetString(
                        Convert.FromBase64String(FrozenCanonicalBase64));
                }
                catch(Exception ex)
                {
                    throw new InvalidOperationException(
                        "V25_CANNOT_PARSE_APPROVED_FROZEN_GENOME",ex);
                }
                core=new NQNativeV25FrozenSignalCore(genes);
                if(core.CanonicalId!=canonical)
                    throw new InvalidOperationException(
                        "V25_FROZEN_CANONICAL_DOES_NOT_MATCH_20_GENES");
                entryTag="V25_"+CandidateId;
                Directory.CreateDirectory(ReportDirectory);
                prefix=Path.Combine(ReportDirectory,
                    entryTag+"_"+HistoricalScope);
                if(File.Exists(prefix+"_bars.tsv")||
                   File.Exists(prefix+"_native_trades.tsv"))
                    throw new InvalidOperationException(
                        "V25_ONE_SHOT_REPORTS_ALREADY_EXIST_DO_NOT_OVERWRITE");
                barWriter=new StreamWriter(new FileStream(
                    prefix+"_bars.tsv",FileMode.CreateNew,
                    FileAccess.Write,FileShare.Read,65536),
                    new UTF8Encoding(false),65536);
                barWriter.WriteLine("V25LockSHA256\t"+FrozenV25LockSHA256);
                barWriter.WriteLine("minuteStartET\topen\thigh\tlow"+
                    "\tclose\tvolume");
                validated=true;
            }
            else if(State==State.Terminated)
            {
                if(barWriter!=null)
                {
                    barWriter.Flush();barWriter.Dispose();barWriter=null;
                }
                if(validated)ExportHistoricalTrades();
            }
        }
        private static string Num(double x)
        {return x.ToString("R",CultureInfo.InvariantCulture);}
        private static string Date(DateTime t)
        {return t.ToString("yyyy-MM-ddTHH:mm:ss",
            CultureInfo.InvariantCulture);}
        private static int Clock(DateTime t)
        {return 10000*t.Hour+100*t.Minute+t.Second;}
        private bool InAuthorizedScope(DateTime start)
        {
            if(HistoricalScope=="DEV")
                return start.Year>=2020&&start.Year<=2022;
            if(HistoricalScope=="EXTERNAL")
                return start.Year>=2023&&start.Year<=2024;
            return start>=new DateTime(2025,1,1)&&
                start<new DateTime(2026,11,1);
        }

        private void UpdateRealizedModel()
        {
            while(closedProcessed<SystemPerformance.AllTrades.Count)
            {
                var t=SystemPerformance.AllTrades[closedProcessed++];
                int side=t.Entry.MarketPosition==MarketPosition.Long?1:
                    t.Entry.MarketPosition==MarketPosition.Short?-1:0;
                if(side==0)throw new InvalidOperationException(
                    "V25_INVALID_NATIVE_ENTRY_DIRECTION");
                closedEquity+=(t.Exit.Price-t.Entry.Price)*side*
                    20.0*t.Quantity-
                    NQNativeV25FrozenSignalCore.ResearchFeeRoundTripUSD*
                    t.Quantity;
            }
        }
        protected override void OnBarUpdate()
        {
            if(BarsInProgress!=0||!validated||
               State!=State.Historical)return; // NEVER live orders.
            if(CurrentBar<0)return;
            DateTime start=NQNativeV25FrozenSignalCore
                .NinjaTraderMinuteStart(Time[0]);
            if(start.Year<2020||start>=new DateTime(2026,11,1))
                return; // strict final holdout cutoff.
            int clock=Clock(start);
            // V16 source and V12 research both use 08:00–11:29 ET.
            // Exclude ETH overnight bars so the native bar export
            // recreates the EXACT V12 source window and ATR seed.
            if(clock<80000||clock>112900)return;
            var bar=new NQBarV11(Open[0],High[0],Low[0],Close[0],
                Volume[0]);
            var signal=core.PushCompletedBar(start,bar);
            if(!InAuthorizedScope(start))return;
            if(day!=start.Date)
            {
                UpdateRealizedModel();
                day=start.Date;sessionStartEquity=closedEquity;
                dailySubmissions=0;
            }
            else UpdateRealizedModel();
            barWriter.WriteLine(String.Join("\t",new[]{
                Date(start),Num(bar.Open),Num(bar.High),Num(bar.Low),
                Num(bar.Close),Num(bar.Volume)
            }));
            if(++exportBars%10000==0)barWriter.Flush();
            if(clock>=NQNativeV25FrozenSignalCore.FlattenSubmit)
            {
                // OnBarClose 11:28 ET -> NT8 market exit next open,
                // normally 11:29 ET as in V12.
                if(Position.MarketPosition==MarketPosition.Long)
                    ExitLong("V25_TIME_FLAT",entryTag);
                else if(Position.MarketPosition==MarketPosition.Short)
                    ExitShort("V25_TIME_FLAT",entryTag);
                return;
            }
            if(clock<NQNativeV25FrozenSignalCore.FirstSignal||
               clock>NQNativeV25FrozenSignalCore.LastSignal||
               Position.MarketPosition!=MarketPosition.Flat||
               dailySubmissions>=genes[15]||
               closedEquity-sessionStartEquity<=-600||
               signal==null)return;

            // Managed NT8 brackets protect a historical 1-contract
            // execution. They DO NOT reproduce V12 adverse SL-first
            // behavior on ambiguous OHLC M1 bars or its entry gap rule.
            // This is precisely why V25 exports and compares fills.
            SetStopLoss(entryTag,CalculationMode.Ticks,
                signal.StopTicks,false);
            if(signal.TargetTicks>0)
                SetProfitTarget(entryTag,CalculationMode.Ticks,
                    signal.TargetTicks);
            if(signal.Side==1)
                EnterLong(1,entryTag);
            else EnterShort(1,entryTag);
            dailySubmissions++;
        }
        private void ExportHistoricalTrades()
        {
            using(var writer=new StreamWriter(new FileStream(
                prefix+"_native_trades.tsv",FileMode.CreateNew,
                FileAccess.Write,FileShare.None),new UTF8Encoding(false)))
            {
                writer.WriteLine("V25LockSHA256\t"+FrozenV25LockSHA256);
                writer.WriteLine("canonicalBase64\tentryET\texitET"+
                    "\tside\tcontracts\tentryPrice\texitPrice"+
                    "\tnativeProfitCurrency\tnetUsingV12Fee");
                foreach(var trade in SystemPerformance.AllTrades)
                {
                    int side=trade.Entry.MarketPosition==MarketPosition.Long?
                        1:-1;
                    int quantity=trade.Quantity;
                    double net=(trade.Exit.Price-trade.Entry.Price)*
                        side*20.0*quantity-
                        NQNativeV25FrozenSignalCore
                        .ResearchFeeRoundTripUSD*quantity;
                    writer.WriteLine(String.Join("\t",new[]{
                        FrozenCanonicalBase64,
                        Date(trade.Entry.Time),Date(trade.Exit.Time),
                        side.ToString(CultureInfo.InvariantCulture),
                        quantity.ToString(CultureInfo.InvariantCulture),
                        Num(trade.Entry.Price),Num(trade.Exit.Price),
                        Num(trade.ProfitCurrency),Num(net)
                    }));
                }
            }
        }
    }
}
