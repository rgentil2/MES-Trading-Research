// V11 source-shim compile and guarded historical execution tests.
// This is NOT NinjaTrader 8 and does NOT validate fill/slippage parity.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
namespace NinjaTrader.Cbi
{
    public enum MarketPosition{Flat,Long,Short}
    public enum EntryHandling{UniqueEntries}
    public enum StopTargetHandling{PerEntryExecution}
    public enum OrderFillResolution{Standard}
    public enum StartBehavior{WaitUntilFlat}
    public enum RealtimeErrorHandling{StopCancelClose}
    public enum CalculationMode{Ticks}
}
namespace NinjaTrader.Data
{
    public enum BarsPeriodType{Minute,Tick}
}
namespace NinjaTrader.NinjaScript
{
    public enum State{SetDefaults,Configure,DataLoaded,Historical,Realtime}
    public enum Calculate{OnBarClose}
    [AttributeUsage(AttributeTargets.Property)]
    public class NinjaScriptPropertyAttribute:Attribute {}
}
namespace NinjaTrader.NinjaScript.Strategies
{
    using NinjaTrader.Cbi;
    using NinjaTrader.Data;
    using NinjaTrader.NinjaScript;
    public sealed class FakeBarsPeriod
    {
        public BarsPeriodType BarsPeriodType{get;set;}=BarsPeriodType.Minute;
        public int Value{get;set;}=1;
    }
    public sealed class FakeMaster
    { public string Name{get;set;}="NQ"; }
    public sealed class FakeInstrument
    { public FakeMaster MasterInstrument{get;set;}=new FakeMaster(); }
    public sealed class FakePosition
    { public MarketPosition MarketPosition{get;set;}=MarketPosition.Flat; }
    public sealed class FakeCurrency
    { public double CumProfit{get;set;}=0; }
    public sealed class FakeTradeStats
    { public FakeCurrency Currency{get;set;}=new FakeCurrency(); }
    public sealed class FakeTrades
    { public FakeTradeStats TradesPerformance{get;set;}=new FakeTradeStats(); }
    public sealed class FakeSystem
    { public FakeTrades AllTrades{get;set;}=new FakeTrades(); }
    public class Strategy
    {
        public string Name{get;set;}
        public string Description{get;set;}
        public Calculate Calculate{get;set;}
        public int EntriesPerDirection{get;set;}
        public EntryHandling EntryHandling{get;set;}
        public bool IsExitOnSessionCloseStrategy{get;set;}
        public int ExitOnSessionCloseSeconds{get;set;}
        public StopTargetHandling StopTargetHandling{get;set;}
        public int BarsRequiredToTrade{get;set;}
        public bool IncludeTradeHistoryInBacktest{get;set;}
        public bool IsInstantiatedOnEachOptimizationIteration{get;set;}
        public OrderFillResolution OrderFillResolution{get;set;}
        public bool IsFillLimitOnTouch{get;set;}
        public bool IncludeCommission{get;set;}
        public int Slippage{get;set;}
        public StartBehavior StartBehavior{get;set;}
        public RealtimeErrorHandling RealtimeErrorHandling{get;set;}
        protected State State{get;set;}
        protected int BarsInProgress{get;set;}=0;
        protected int CurrentBar{get;set;}=0;
        protected FakeBarsPeriod BarsPeriod{get;set;}=new FakeBarsPeriod();
        protected FakeInstrument Instrument{get;set;}=new FakeInstrument();
        protected FakePosition Position{get;set;}=new FakePosition();
        protected FakeSystem SystemPerformance{get;set;}=new FakeSystem();
        protected DateTime[] Time{get;set;}=new DateTime[1];
        protected double[] Open{get;set;}=new double[1];
        protected double[] High{get;set;}=new double[1];
        protected double[] Low{get;set;}=new double[1];
        protected double[] Close{get;set;}=new double[1];
        protected double[] Volume{get;set;}=new double[1];
        protected double TickSize{get;set;}=0.25;
        public readonly List<string> History=new List<string>();
        protected virtual void OnStateChange(){}
        protected virtual void OnBarUpdate(){}
        protected void Print(string msg){History.Add(msg);}
        protected static int ToTime(DateTime d)
        { return d.Hour*10000+d.Minute*100+d.Second; }
        protected double[] ATR(int n){return new[]{2.0};}
        protected void SetStopLoss(CalculationMode mode,int tick)
        { History.Add("FixedStop="+tick); }
        protected void SetProfitTarget(CalculationMode mode,int tick)
        { History.Add("FixedTarget="+tick); }
        protected void SetStopLoss(string signal,CalculationMode mode,
            int tick,bool simulated)
        { History.Add("DynamicStop="+tick); }
        protected void SetProfitTarget(string signal,CalculationMode mode,int tick)
        { History.Add("DynamicTarget="+tick); }
        protected void EnterLong(int quantity,string tag)
        { History.Add("ENTER_LONG");Position.MarketPosition=MarketPosition.Long; }
        protected void EnterShort(int quantity,string tag)
        { History.Add("ENTER_SHORT");Position.MarketPosition=MarketPosition.Short; }
        protected void ExitLong(string tag,string from)
        { History.Add("EXIT_LONG");Position.MarketPosition=MarketPosition.Flat; }
        protected void ExitShort(string tag,string from)
        { History.Add("EXIT_SHORT");Position.MarketPosition=MarketPosition.Flat; }
        public void SimState(State state){State=state;OnStateChange();}
        public void SimInstrument(string symbol){Instrument.MasterInstrument.Name=symbol;}
        public void SimPeriod(int minutes){BarsPeriod.Value=minutes;}
        public void SimBar(DateTime date,double o,double h,double l,double c,
                           double v,bool realtime=false)
        {
            State=realtime?State.Realtime:State.Historical;
            CurrentBar++;
            Time[0]=date;Open[0]=o;High[0]=h;Low[0]=l;
            Close[0]=c;Volume[0]=v;
            OnBarUpdate();
        }
    }
}
internal static class V11RealStrategyShimTest
{
    private static void A(bool ok,string why)
    {if(!ok)throw new Exception("V11_STRATEGY_SHIM_FAIL "+why);}
    private static NQNativeSignalLabV11 NewStrategy(int year)
    {
        var s=new NQNativeSignalLabV11();
        s.SimState(NinjaTrader.NinjaScript.State.SetDefaults);
        A(s.Name=="NQNativeSignalLabV11","strategy name");
        A(s.IncludeCommission&&s.Slippage==2,"simulation cost assumptions");
        s.ConditionCount=1;s.AType=0;s.APeriod=6;
        s.ExitMode=0;s.StopTicks=20;s.TargetTicks=32;
        s.SimState(NinjaTrader.NinjaScript.State.DataLoaded);
        A(s.CanonicalReady && !s.IsStructurallyRedundant &&
          s.EffectiveConditionCount==1,"canonical runtime metadata");
        A(s.CanonicalRuntimeFingerprint.StartsWith("NQEX11_"),
          "V11 disjoint IDs");
        s.SimState(NinjaTrader.NinjaScript.State.Configure);
        A(s.History.Contains("FixedStop=20")&&
          s.History.Contains("FixedTarget=32"),"protective orders installed");
        return s;
    }
    private static void Feed(NQNativeSignalLabV11 s,int year,int count)
    {
        double price=15000;
        var date=new DateTime(year,6,1,9,30,0);
        for(int i=0;i<count;i++)
        {
            double op=price;price+=3.0+Math.Sin(i/4.0)*0.3;
            s.SimBar(date.AddMinutes(i),op,Math.Max(op,price)+1,
                     Math.Min(op,price)-1,price,400);
        }
    }
    public static int Main()
    {
        var source=NewStrategy(2021);
        Feed(source,2021,120);
        A(source.History.Contains("ENTER_LONG"),
          "synthetic 2021 directional signals must trigger a protected entry");
        A(source.History.Contains("EXIT_LONG"),
          "11:28 flatten must trigger on historical bar");
        A(source.History.Count(x=>x=="ENTER_LONG")<=2,
          "max two daily submissions");
        A(source.History.All(x=>x!="ENTER_SHORT"),
          "monotonic synthetic trend must not be short");
        var outOfSample=NewStrategy(2023);
        Feed(outOfSample,2023,120);
        A(!outOfSample.History.Any(x=>x.StartsWith("ENTER")),
          "2023 withheld from development");
        var wrong=NewStrategy(2021);
        wrong.SimInstrument("ES");
        Feed(wrong,2021,120);
        A(!wrong.History.Any(x=>x.StartsWith("ENTER")),
          "reject non NQ instrument");
        var future=NewStrategy(2021);
        var now=new DateTime(2021,6,1,9,45,0);
        future.SimBar(now,100,102,99,101,100,true);
        A(!future.History.Any(x=>x.StartsWith("ENTER")),
          "realtime orders must be blocked");
        Console.WriteLine("NQ_V11_NATIVE_STRATEGY_SOURCE_SHIM_PASS "+
          "RESEARCH_ONLY_2020_22_NQ_M1_RTH_DAILY_CAP_EXIT");
        Console.WriteLine("REAL_NINJATRADER_WINDOWS_COMPILE_NOT_TESTED");
        return 0;
    }
}
