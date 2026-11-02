// S0.64 CI-only simulation of native NinjaTrader API surfaces used by G0.
// This does NOT stand in for actual NinjaTrader compilation on Windows.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
namespace NinjaTrader.Cbi
{
    public enum PrintTo {OutputTab1}
    public class Execution {public DateTime Time {get;set;}}
    public class Trade
    {
        public Execution Entry {get;set;}
        public Execution Exit {get;set;}
        public double ProfitCurrency {get;set;}
    }
}
namespace NinjaTrader.Code
{
    public static class Output
    {
        public static List<string> Lines=new List<string>();
        public static void Process(string t,NinjaTrader.Cbi.PrintTo tab)
        { Lines.Add(t); }
    }
}
namespace NinjaTrader.NinjaScript
{
    public class Results
    {
        public double NetProfit {get;set;}
    }
    public class TradesCollection
    {
        private List<NinjaTrader.Cbi.Trade> data=new List<NinjaTrader.Cbi.Trade>();
        public int Count {get{return data.Count;}}
        public NinjaTrader.Cbi.Trade this[int i]{get{return data[i];}}
        public Results TradesPerformance {get;set;}=new Results();
        public void Add(NinjaTrader.Cbi.Trade t)
        { data.Add(t);TradesPerformance.NetProfit+=t.ProfitCurrency; }
    }
    public class SystemPerformanceData
    {
        public TradesCollection AllTrades {get;set;}=new TradesCollection();
    }
    public class StrategyBase
    {
        public SystemPerformanceData SystemPerformance {get;set;}=new SystemPerformanceData();
    }
    public class OptimizationFitness
    {
        public double Value {get;protected set;}
        protected virtual void OnCalculatePerformanceValue(StrategyBase s){}
        public void Calculate(StrategyBase s){OnCalculatePerformanceValue(s);}
    }
}
namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQNativeGeneticLabV5 : NinjaTrader.NinjaScript.StrategyBase
    {
        public bool CanonicalReady{get;set;}=true;
        public bool IsStructurallyRedundant{get;set;}
        public int EffectiveConditionCount{get;set;}=2;
        public string CanonicalRuntimeFingerprint{get;set;}="NQEX5_CI";
    }
}
internal static class AdapterTest
{
    private static void T(bool x,string what)
    {if(!x)throw new Exception("FAIL G0 native shim "+what);}
    private static NQNativeGeneticLabV5 Scenario(double win,double loss)
    {
        var s=new NQNativeGeneticLabV5();
        for(int y=2020;y<=2022;y++)
          for(int m=1;m<=12;m++)
            for(int k=0;k<5;k++)
            {
                var dt=new DateTime(y,m,1,9,50,0).AddMinutes(k*2);
                s.SystemPerformance.AllTrades.Add(new NinjaTrader.Cbi.Trade{
                    Entry=new NinjaTrader.Cbi.Execution{Time=dt},
                    Exit=new NinjaTrader.Cbi.Execution{Time=dt.AddMinutes(1)},
                    ProfitCurrency=k==4?loss:win
                });
            }
        return s;
    }
    public static int Main()
    {
        var fitness=new NinjaTrader.NinjaScript.OptimizationFitnesses.NQNativeG0FitnessV6();
        fitness.Calculate(Scenario(25,-25));
        T(Math.Abs(fitness.Value-2700)<0.01,"pass eligible");
        T(NinjaTrader.Code.Output.Lines.Any(x=>x.Contains("PASS") &&
          x.Contains("monthsBelow5=0")),"pass runtime logging");
        fitness.Calculate(Scenario(27,-100));
        T(fitness.Value==NQNativeG0RulesV6.RejectScore,"PF fail");
        var blocked=Scenario(25,-25);blocked.IsStructurallyRedundant=true;
        fitness.Calculate(blocked);
        T(fitness.Value==NQNativeG0RulesV6.RejectScore,"structural fail");
        var mismatch=Scenario(25,-25);
        mismatch.SystemPerformance.AllTrades.TradesPerformance.NetProfit+=1;
        fitness.Calculate(mismatch);
        T(fitness.Value==NQNativeG0RulesV6.RejectScore,"net mismatch fail");
        T(NinjaTrader.Code.Output.Lines.Any(x=>x.Contains("PNL_MISMATCH")),"mismatch diagnostic");
        Console.WriteLine("NQ_S064_G0_NATIVE_FITNESS_SHIM_QA_PASS=5");
        Console.WriteLine("ACTUAL_NINJATRADER_WIN_F5_COMPILE_STILL_REQUIRED");
        return 0;
    }
}
