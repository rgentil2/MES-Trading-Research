// V25 API SHAPE STUB ONLY for C# syntax and safety gating.
// This file is NEVER copied into NinjaTrader and is NOT a substitute
// for compiling against the real NinjaTrader 8 DLL/API at final V25.
// It deliberately exercises only the subset our validation Strategy
// references, so any vendor-version mismatch remains to verify later.
using System;
using System.Collections.Generic;
namespace NinjaTrader.Cbi
{
    public enum MarketPosition{Flat,Long,Short}
    public class ExecutionRecord
    {
        public MarketPosition MarketPosition;
        public double Price;
        public DateTime Time;
    }
    public class Trade
    {
        public ExecutionRecord Entry=new ExecutionRecord();
        public ExecutionRecord Exit=new ExecutionRecord();
        public int Quantity=1;
        public double ProfitCurrency;
    }
}
namespace NinjaTrader.Data
{
    public enum BarsPeriodType{Minute,Day}
    public class BarsPeriod
    {
        public BarsPeriodType BarsPeriodType;
        public int Value;
    }
}
namespace NinjaTrader.NinjaScript
{
    public enum State{SetDefaults,Configure,DataLoaded,Historical,Realtime,Terminated}
    public enum Calculate{OnBarClose}
    public enum EntryHandling{AllEntries}
    public enum StartBehavior{WaitUntilFlat}
    public enum CalculationMode{Ticks}
    [AttributeUsage(AttributeTargets.Property)]
    public class NinjaScriptPropertyAttribute:Attribute{}
    public class InstrumentInfo{public string FullName="NQ 12-26";}
    public class PositionInfo
    {
        public NinjaTrader.Cbi.MarketPosition MarketPosition=
            NinjaTrader.Cbi.MarketPosition.Flat;
    }
    public class SystemPerformanceInfo
    {
        public List<NinjaTrader.Cbi.Trade> AllTrades=
            new List<NinjaTrader.Cbi.Trade>();
    }
    public class TSeries<T>
    {
        public T Current;
        public T this[int barsAgo]{get{return Current;}}
    }
    public class Strategy
    {
        public string Name,Description;
        public State State;
        public Calculate Calculate;
        public EntryHandling EntryHandling;
        public int EntriesPerDirection,Slippage,BarsRequiredToTrade;
        public bool IsExitOnSessionCloseStrategy;
        public bool IsInstantiatedOnEachOptimizationIteration;
        public bool IncludeTradeHistoryInBacktest,IncludeCommission;
        public bool IsInStrategyAnalyzer;
        public StartBehavior StartBehavior;
        public int BarsInProgress,CurrentBar;
        public NinjaTrader.Data.BarsPeriod BarsPeriod=
            new NinjaTrader.Data.BarsPeriod{
                BarsPeriodType=NinjaTrader.Data.BarsPeriodType.Minute,
                Value=1};
        public InstrumentInfo Instrument=new InstrumentInfo();
        public PositionInfo Position=new PositionInfo();
        public SystemPerformanceInfo SystemPerformance=
            new SystemPerformanceInfo();
        public TSeries<DateTime> Time=new TSeries<DateTime>();
        public TSeries<double> Open=new TSeries<double>();
        public TSeries<double> High=new TSeries<double>();
        public TSeries<double> Low=new TSeries<double>();
        public TSeries<double> Close=new TSeries<double>();
        public TSeries<double> Volume=new TSeries<double>();
        public int OrdersSubmitted;
        protected virtual void OnStateChange(){}
        protected virtual void OnBarUpdate(){}
        public void Invoke(State s)
        {
            State=s;
            OnStateChange();
        }
        public void Replay(DateTime minuteEnd,double o,double h,
            double l,double c,double vol)
        {
            CurrentBar++;
            Time.Current=minuteEnd;
            Open.Current=o;High.Current=h;Low.Current=l;
            Close.Current=c;Volume.Current=vol;
            OnBarUpdate();
        }
        protected void SetStopLoss(string name,CalculationMode mode,
            double ticks,bool sim){}
        protected void SetProfitTarget(string name,CalculationMode mode,
            double ticks){}
        protected void EnterLong(int quantity,string name)
        {OrdersSubmitted++;}
        protected void EnterShort(int quantity,string name)
        {OrdersSubmitted++;}
        protected void ExitLong(string signal,string entry)
        {OrdersSubmitted++;}
        protected void ExitShort(string signal,string entry)
        {OrdersSubmitted++;}
    }
}
internal static class V25NativeSyntaxHarness
{
    static void A(bool ok,string reason)
    {if(!ok)throw new Exception("NQ_V25_NT8_API_STUB_FAIL "+reason);}
    public static int Main()
    {
        var script=new NinjaTrader.NinjaScript.Strategies.NQ_V25_FrozenAnalyzer();
        script.Invoke(NinjaTrader.NinjaScript.State.SetDefaults);
        A(!script.ArmHistoricalValidation,
          "native strategy must be disarmed by default");
        script.Invoke(NinjaTrader.NinjaScript.State.Configure);
        A(script.IncludeTradeHistoryInBacktest&&script.IncludeCommission,
          "native Strategy Analyzer trade receipts and commissions enabled");
        script.Invoke(NinjaTrader.NinjaScript.State.DataLoaded);
        script.Invoke(NinjaTrader.NinjaScript.State.Historical);
        script.Replay(new DateTime(2020,1,1,9,31,0),
            15000,15001,14999,15000,500);
        A(script.OrdersSubmitted==0,
          "unarmed historical never submits an order");
        script.Invoke(NinjaTrader.NinjaScript.State.Realtime);
        script.Replay(new DateTime(2020,1,1,9,32,0),
            15000,15001,14999,15000,500);
        A(script.OrdersSubmitted==0,
          "unarmed realtime never submits an order");
        var prohibited=new NinjaTrader.NinjaScript.Strategies
            .NQ_V25_FrozenAnalyzer();
        prohibited.Invoke(NinjaTrader.NinjaScript.State.SetDefaults);
        prohibited.ArmHistoricalValidation=true;
        prohibited.IsInStrategyAnalyzer=false;
        try
        {
            prohibited.Invoke(NinjaTrader.NinjaScript.State.DataLoaded);
            throw new Exception("V25_ALLOWED_NON_ANALYZER_CHART");
        }
        catch(InvalidOperationException ex)
        {A(ex.Message.Contains("ONLY_STRATEGY_ANALYZER"),
            "armed V25 must reject live chart contexts");}
        var locked=new NinjaTrader.NinjaScript.Strategies
            .NQ_V25_FrozenAnalyzer();
        locked.Invoke(NinjaTrader.NinjaScript.State.SetDefaults);
        locked.ArmHistoricalValidation=true;
        locked.ConfirmEndStampedET=true;
        locked.IsInStrategyAnalyzer=true;
        locked.HistoricalScope="FINAL";
        locked.FrozenV25LockSHA256=new string('a',64);
        locked.CandidateId="NQ-00001";
        int[] genome={1,396,12,789,12,999,12,1319,12,
            0,0,0,0,20,32,2,0,14,15,25};
        locked.FrozenGenes20=String.Join("/",genome);
        locked.FrozenCanonicalBase64=Convert.ToBase64String(
            System.Text.Encoding.UTF8.GetBytes(
                NinjaTrader.NinjaScript.Strategies
                .NQNativeExitCanonicalV19.Analyze(genome).RuntimeKey));
        locked.ReportDirectory=System.IO.Path.GetTempPath();
        string handoff=System.IO.Path.Combine(
            System.IO.Path.GetTempPath(),"V25_HANDOFF_STUB_"+
            Guid.NewGuid().ToString("N")+".tsv");
        try
        {
            string handoffBody=
                "V25LockSHA256\t"+locked.FrozenV25LockSHA256+"\n"+
                "V23ArtifactsSHA256\t"+new string('b',64)+"\n"+
                "sourceBarsSHA256\t"+new string('c',64)+"\n"+
                "frozenCampaignDigest\t"+new string('d',64)+"\n"+
                "candidateId\tcanonicalBase64\tgenes20\n"+
                "NQ-00001\t"+locked.FrozenCanonicalBase64+"\t"+
                    locked.FrozenGenes20+"\n"+
                "NQ-00002\t"+locked.FrozenCanonicalBase64+"\t"+
                    locked.FrozenGenes20+"\n"+
                "NQ-00003\t"+locked.FrozenCanonicalBase64+"\t"+
                    locked.FrozenGenes20+"\n";
            System.IO.File.WriteAllText(handoff,handoffBody+
                "handoffContentSHA256\t"+
                NinjaTrader.NinjaScript.Strategies
                    .NQNativeReproducibilityV23.SHA(handoffBody)+"\n");
            locked.FrozenHandoffFile=handoff;
            try
            {
                locked.Invoke(NinjaTrader.NinjaScript.State.DataLoaded);
                throw new Exception("V25_FINAL_WITHOUT_EXTERNAL_PASSED");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("PREVIOUS_NATIVE_GATE_SHA"),
                "native adapter forbids final until signed prior stage exists");}
            locked.HistoricalScope="DEV";
            locked.FrozenGenes20=String.Join("/",new[]{
                1,407,12,789,12,999,12,1319,12,
                0,0,0,0,20,32,2,0,14,15,25});
            locked.FrozenCanonicalBase64=Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes(
                    NinjaTrader.NinjaScript.Strategies
                    .NQNativeExitCanonicalV19.Analyze(
                        new[]{1,407,12,789,12,999,12,1319,12,
                            0,0,0,0,20,32,2,0,14,15,25}).RuntimeKey));
            try
            {
                locked.Invoke(NinjaTrader.NinjaScript.State.DataLoaded);
                throw new Exception("V25_REPLACED_FROZEN_GENES_ACCEPTED");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("NATIVE_GENES_NOT_IN_VERIFIED"),
                "native adapter must use exact 20 handoff genes");}
            // Restore the approved candidate identity but modify its
            // handoff bytes without regenerating the canonical SHA:
            // native adapter must reject before any historical entry.
            locked.FrozenGenes20=String.Join("/",genome);
            locked.FrozenCanonicalBase64=Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes(
                    NinjaTrader.NinjaScript.Strategies
                    .NQNativeExitCanonicalV19.Analyze(genome).RuntimeKey));
            System.IO.File.AppendAllText(handoff,"TAMPER");
            try
            {
                locked.Invoke(NinjaTrader.NinjaScript.State.DataLoaded);
                throw new Exception("V25_ACCEPTED_MODIFIED_HANDOFF_SHA");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("HANDOFF_CONTENT_SHA_CHANGED"),
                "native handoff file SHA must detect changed gene rows");}
        }
        finally
        {if(System.IO.File.Exists(handoff))System.IO.File.Delete(handoff);}
        Console.WriteLine("NQ_V25_NT8_API_STUB_PASS "+
            "syntaxCompiledWithSurrogate=TRUE"+
            " defaultDisabled=TRUE noLiveChartActivation=TRUE"+
            " finalWithoutExternalDenied=TRUE"+
            " changedGeneHandoffRejected=TRUE"+
            " modifiedHandoffSHARejected=TRUE"+
            " note=NOT_A_REAL_NINJATRADER_DLL_COMPILATION");
        return 0;
    }
}
