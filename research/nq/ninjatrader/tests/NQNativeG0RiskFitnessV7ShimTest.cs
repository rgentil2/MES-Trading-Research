// S0.66 NQ V7 fitness build against a STRICT NT8 API shim.
// Does NOT certify actual NinjaTrader/Windows assembly compilation.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
namespace NinjaTrader.Cbi
{
    public enum PrintTo { OutputTab1 }
    public class Execution { public DateTime Time {get;set;} }
    public class Trade
    {
        public Execution Entry {get;set;}
        public Execution Exit {get;set;}
        public double ProfitCurrency {get;set;}
        public double MaeCurrency {get;set;}
        public double MfeCurrency {get;set;}
    }
}
namespace NinjaTrader.Code
{
    public static class Output
    {
        public static readonly List<string> Lines=new List<string>();
        public static void Process(string s,NinjaTrader.Cbi.PrintTo to)
        {Lines.Add(s);}
    }
}
namespace NinjaTrader.NinjaScript
{
    public class TradePerformanceResults {public double NetProfit {get;set;}}
    public class TradesCollection
    {
        public readonly List<NinjaTrader.Cbi.Trade> Data=
            new List<NinjaTrader.Cbi.Trade>();
        public int Count {get{return Data.Count;}}
        public NinjaTrader.Cbi.Trade this[int n]{get{return Data[n];}}
        public TradePerformanceResults TradesPerformance {get;set;}=
            new TradePerformanceResults();
        public void Add(NinjaTrader.Cbi.Trade t)
        { Data.Add(t);TradesPerformance.NetProfit+=t.ProfitCurrency;}
    }
    public class SystemPerformanceData
    {
        public TradesCollection AllTrades {get;set;}=
            new TradesCollection();
    }
    public class StrategyBase
    {
        public SystemPerformanceData SystemPerformance {get;set;}=
            new SystemPerformanceData();
    }
    public class OptimizationFitness
    {
        public double Value {get; protected set;}
        protected virtual void OnCalculatePerformanceValue(StrategyBase s){}
        public void Calculate(StrategyBase s){OnCalculatePerformanceValue(s);}
    }
}
namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQNativeGeneticLabV5:NinjaTrader.NinjaScript.StrategyBase
    {
        public bool CanonicalReady {get;set;}=true;
        public bool IsStructurallyRedundant {get;set;}=false;
        public int EffectiveConditionCount {get;set;}=2;
        public string CanonicalRuntimeFingerprint {get;set;}="NQEX5_SIM";
    }
}
internal static class NativeShimTest
{
    static int checks;
    static void T(bool a,string msg)
    {checks++;if(!a)throw new Exception("V7 native shim "+msg);}
    static NQNativeGeneticLabV5 Scenario(double winner=25,double loser=-25,
                                           double mae=20,double mfe=5)
    {
        var s=new NQNativeGeneticLabV5();
        for(int y=2020;y<=2022;y++)
        for(int m=1;m<=12;m++)
        for(int j=0;j<5;j++)
        {
            var dt=new DateTime(y,m,1,9,50,0).AddMinutes(j*3);
            s.SystemPerformance.AllTrades.Add(new NinjaTrader.Cbi.Trade{
                Entry=new NinjaTrader.Cbi.Execution{Time=dt},
                Exit=new NinjaTrader.Cbi.Execution{Time=dt.AddMinutes(1)},
                ProfitCurrency=j==4?loser:winner,
                MaeCurrency=mae,MfeCurrency=mfe
            });
        }
        return s;
    }
    public static int Main()
    {
        var f=new NinjaTrader.NinjaScript.OptimizationFitnesses.NQNativeG0RiskFitnessV7();
        var good=Scenario();
        f.Calculate(good);
        T(Math.Abs(f.Value-2700)<0.01,"positive V7 eligible score");
        T(NinjaTrader.Code.Output.Lines.Any(x=>x.Contains("NQ_G0_V7 PASS") &&
          x.Contains("stressDD=")),"pass diagnostics");
        var bad=Scenario(27,-100,3200,100);
        f.Calculate(bad);
        T(f.Value==NQNativeG0RulesV6.RejectScore,"bad economic & stress");
        T(NinjaTrader.Code.Output.Lines.Any(x=>x.Contains("NQ_G0_V7 REJECT")
            && x.Contains("EXCESS_M1_MAE_MFE_STRESS_DD")
            && x.Contains("LOW_PROFIT_FACTOR")),"multiple rejection reasons");
        var mismatch=Scenario();
        mismatch.SystemPerformance.AllTrades.TradesPerformance.NetProfit+=10;
        f.Calculate(mismatch);
        T(f.Value==NQNativeG0RulesV6.RejectScore,"native mismatch fail closed");
        T(NinjaTrader.Code.Output.Lines.Any(x=>x.Contains("PNL_MISMATCH")),
          "native mismatch reason logged");
        var invalid=Scenario();
        invalid.SystemPerformance.AllTrades.Data[0].MaeCurrency=double.NaN;
        f.Calculate(invalid);
        T(f.Value==NQNativeG0RulesV6.RejectScore,"corrupt MAE fail closed");
        T(NinjaTrader.Code.Output.Lines.Any(x=>x.Contains("INVALID_MAE_MFE")),
          "invalid MAE diagnostic");
        var redundant=Scenario();redundant.IsStructurallyRedundant=true;
        f.Calculate(redundant);
        T(f.Value==NQNativeG0RulesV6.RejectScore,"redundant rejected");
        T(NinjaTrader.Code.Output.Lines.Any(x=>x.Contains("INVALID_OR_REDUNDANT")),
          "redundancy diagnostic");
        Console.WriteLine("NQ_S066_G0_V7_NT8_API_SHIM_QA_PASS="+checks);
        Console.WriteLine("WINDOWS_NINJATRADER_F5_AND_20_REAL_BACKTESTS_PENDING");
        return 0;
    }
}
