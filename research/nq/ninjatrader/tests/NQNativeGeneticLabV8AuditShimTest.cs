// S0.68: compile/behavior SIMULATOR for the production V8 observer.
// This is NOT NinjaTrader; a real NT8 F5 compile and parity replay are required.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.Cbi
{
    public enum MarketPosition{Flat,Long,Short}
    public enum PerformanceUnit{Currency}
}
namespace NinjaTrader.Data
{
    public enum BarsPeriodType{Minute}
}
namespace NinjaTrader.NinjaScript
{
    public enum State{SetDefaults,Configure,DataLoaded,Historical,Terminated}
}
namespace NinjaTrader.NinjaScript.Strategies
{
    using NinjaTrader.Cbi;
    using NinjaTrader.Data;
    using NinjaTrader.NinjaScript;
    public class FakeBarPeriod{public BarsPeriodType BarsPeriodType{get;set;}=BarsPeriodType.Minute;public int Value{get;set;}=1;}
    public class FakeMaster{public string Name{get;set;}="NQ";}
    public class FakeInstrument{public FakeMaster MasterInstrument{get;set;}=new FakeMaster();}
    public class FakePosition
    {
        public MarketPosition MarketPosition{get;set;}=MarketPosition.Flat;
        public double GetUnrealizedProfitLoss(PerformanceUnit unit,double px)
        {return MarketPosition==MarketPosition.Flat?0:MarketPosition==MarketPosition.Long?(px-100)*20:(100-px)*20;}
    }
    public class FakeTradeEntry{public DateTime Time{get;set;}}
    public class FakeTrade{public FakeTradeEntry Entry{get;set;}=new FakeTradeEntry();}
    public class FakeCurrency{public double CumProfit{get;set;}}
    public class FakePerformance{public FakeCurrency Currency{get;set;}=new FakeCurrency();}
    public class FakeTrades
    {
        public readonly List<FakeTrade> All=new List<FakeTrade>();
        public FakePerformance TradesPerformance{get;set;}=new FakePerformance();
        public int Count{get{return All.Count;}}
        public FakeTrade this[int i]{get{return All[i];}}
    }
    public class FakeSystem{public FakeTrades AllTrades{get;set;}=new FakeTrades();}
    public class NQNativeGeneticLabV5
    {
        public readonly List<string> Logs=new List<string>();
        public string Name{get;set;}
        public string Description{get;set;}
        public State State{get;set;}
        public int BarsInProgress{get;set;}
        public int CurrentBar{get;set;}
        public DateTime[] Time{get;set;}=new DateTime[1];
        public double[] Close{get;set;}=new[]{102.0};
        public FakeBarPeriod BarsPeriod{get;set;}=new FakeBarPeriod();
        public FakeInstrument Instrument{get;set;}=new FakeInstrument();
        public FakePosition Position{get;set;}=new FakePosition();
        public FakeSystem SystemPerformance{get;set;}=new FakeSystem();
        public string CanonicalRuntimeFingerprint{get;set;}="NQEX5_SIMULATED";
        public int ConditionCount{get;set;}=1;
        public int AType{get;set;}=5;
        public int APeriod{get;set;}=6;
        public int BType{get;set;}=6;
        public int BPeriod{get;set;}=6;
        public int CType{get;set;}=4;
        public int CPeriod{get;set;}=18;
        public int DType{get;set;}=6;
        public int DPeriod{get;set;}=30;
        public int CombineAB{get;set;}
        public int CombineBC{get;set;}
        public int CombineCD{get;set;}
        public int ReverseSignals{get;set;}
        public int StopTicks{get;set;}=20;
        public int TargetTicks{get;set;}=32;
        public int MaxDailyEntrySubmissions{get;set;}=2;
        public int ExitMode{get;set;}=0;
        public int ATRPeriod{get;set;}=14;
        public int ATRStopX10{get;set;}=15;
        public int ATRTargetX10{get;set;}=25;
        public double TickSize{get;set;}=0.25;
        public int BaseOnBarCalls{get;private set;}
        protected virtual void OnStateChange(){}
        protected virtual void OnBarUpdate(){BaseOnBarCalls++;}
        protected void Print(string s){Logs.Add(s);}
        protected int ToTime(DateTime dt){return dt.Hour*10000+dt.Minute*100+dt.Second;}
        protected double[] SMA(double[] src,int n){return new[]{100.0,100.0};}
        protected double[] EMA(double[] src,int n){return new[]{100.0,100.0};}
        protected double[] WMA(double[] src,int n){return new[]{100.0,100.0};}
        protected double[] RSI(double[] src,int n,int smooth){return new[]{60.0,55.0};}
        protected double[] CCI(double[] src,int n){return new[]{110.0,50.0};}
        protected double[] ATR(int n){return new[]{4.0};}
        public void FakeState(State s){State=s;OnStateChange();}
        public void FakeBar(DateTime dt,int index,double px=102)
        {
            State=State.Historical;Time[0]=dt;CurrentBar=index;Close[0]=px;
            OnBarUpdate();
        }
    }
    public static class NQNativeATRExitMathV5
    {
        public static bool TryCompute(int mode,double atr,double tick,
            int stop,int target,int stopX10,int targetX10,
            out int stopTicks,out int targetTicks)
        {
            stopTicks=mode==0?stop:(int)Math.Ceiling(atr*stopX10/10.0/tick);
            targetTicks=mode==0?target:(int)Math.Ceiling(atr*targetX10/10.0/tick);
            return stopTicks>0;
        }
    }
}
internal static class V8ShimQA
{
    static int assertions;
    static void T(bool yes,string why)
    {assertions++;if(!yes)throw new Exception("V8 shims QA FAIL "+why);}
    public static void Main()
    {
        var v=new NinjaTrader.NinjaScript.Strategies.NQNativeGeneticLabV8Audit();
        v.FakeState(NinjaTrader.NinjaScript.State.SetDefaults);
        T(v.Name=="NQNativeGeneticLabV8Audit","distinct strategy name");
        v.FakeState(NinjaTrader.NinjaScript.State.DataLoaded);
        int call=0;
        for(int yr=2020;yr<=2022;yr++)
            for(int m=0;m<130;m++)
            {
                v.FakeBar(new DateTime(yr,1,4,9,30,0).AddMinutes(m),call);
                call++;
            }
        T(v.BaseOnBarCalls==390,"V5 base called exactly once per M1 bar");
        v.FakeState(NinjaTrader.NinjaScript.State.Terminated);
        T(v.Logs.Count(x=>x.StartsWith("NQ_V8_FREQ"))==3,"three yearly frequency reports");
        T(v.Logs.Count(x=>x.StartsWith("NQ_V8_RISK"))==3,"three yearly risk reports");
        T(v.Logs.Count(x=>x.StartsWith("NQ_V8_MONTH"))==12,"twelve 2022 monthly diagnostics");
        T(v.Logs.Any(x=>x.StartsWith("NQ_V8_END")),"one end report");
        T(v.Logs.Any(x=>x.Contains("year=2022") && x.Contains("rawDirectional=")),"2022 raw diagnosis");
        T(v.Logs.Any(x=>x.Contains("predictedSubmissions=2")),"daily cap prediction observable");
        T(v.Logs.Any(x=>x.Contains("globalBarCloseMaxDD=0.00")),"flat equity test");
        T(v.Logs.Any(x=>x.Contains("actualCompletedTrades=0")),"no fake order side effects");
        Console.WriteLine("NQ_S068_V8_NATIVE_API_SHIM_TESTS_PASS="+assertions);
        Console.WriteLine("REAL_NINJATRADER_F5_AND_V5_PARITY_20_REPLAY_PENDING");
    }
}
