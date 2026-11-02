// S0.54 CI-only NinjaTrader API SHIM. NOT production NT8 assemblies.
// Ensures the adapter C# is syntactically valid and that in a controlled
// simulated Optimizer Value/Min/Max/Increment contract it fails safely,
// does not run duplicates, and writes the requested strategy gene values.
// Actual NinjaTrader runtime Parameter ABI remains unverified in Windows.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

namespace NinjaTrader.Cbi { public enum PrintTo { OutputTab1, OutputTab2 } }
namespace NinjaTrader.Code {
    public static class Output {
        public static readonly List<string> Logs=new List<string>();
        public static void Process(string m,NinjaTrader.Cbi.PrintTo tab) { Logs.Add(m); }
    }
}
namespace NinjaTrader.NinjaScript {
    public enum State { SetDefaults,Configure,DataLoaded,Historical }
    [AttributeUsage(AttributeTargets.Property)]
    public sealed class NinjaScriptPropertyAttribute : Attribute {}
    public class Parameter {
        public string Name {get;set;}
        public int Min {get;set;}
        public int Max {get;set;}
        public int Increment {get;set;}
        public int Value {get;set;}
    }
    public class StrategyBase {
        public List<object> OptimizationParameters {get;set;}
            =new List<object>();
    }
    public abstract class Optimizer {
        protected State State {get;set;}
        protected List<StrategyBase> Strategies {get;set;}
            =new List<StrategyBase>();
        protected string Name {get;set;}
        protected int NumberOfIterations {get;set;}
        public int Executed {get;private set;}
        public readonly List<string> Ids=new List<string>();
        protected virtual void OnStateChange(){}
        protected abstract void OnOptimize();
        protected void RunIteration() {
            Executed++;
            var s=(NQNativeGeneticLabV3)Strategies[0];
            var genes=typeof(NQUniqueSearchV4).GetField("Names") != null
                ? NQUniqueSearchV4.Names.Select(n=>
                    (int)typeof(NQNativeGeneticLabV3).GetProperty(n).GetValue(s,null)).ToArray()
                : new int[0];
            var id=NQUniqueSearchV4.AnalyzeGenes(genes);
            if(id.IsRedundant)throw new Exception("Adapter sent redundant structure to RunIteration");
            if(!Ids.Contains(id.RuntimeKey))Ids.Add(id.RuntimeKey);
            else throw new Exception("Adapter reran an equivalent fingerprint");
            foreach(Parameter p in s.OptimizationParameters)
                if(p.Name=="ConditionCount" && p.Value!=s.ConditionCount)
                    throw new Exception("Parameter/Strategy out of sync");
        }
        public void Simulate(NQNativeGeneticLabV3 strategy,int wanted,int seed,int maxAttempts) {
            State=State.SetDefaults;OnStateChange();
            Strategies.Add(strategy);
            var t=GetType();
            t.GetProperty("UniqueCandidates").SetValue(this,wanted,null);
            t.GetProperty("Seed").SetValue(this,seed,null);
            t.GetProperty("MaxAttempts").SetValue(this,maxAttempts,null);
            State=State.Configure;OnStateChange();
            OnOptimize();
        }
    }
}
namespace NinjaTrader.NinjaScript.Strategies {
    public class NQNativeGeneticLabV3 : NinjaTrader.NinjaScript.StrategyBase {
        public int ConditionCount {get;set;}=2;
        public int AType {get;set;}=2;
        public int APeriod {get;set;}=18;
        public int BType {get;set;}=7;
        public int BPeriod {get;set;}=6;
        public int CType {get;set;}=2;
        public int CPeriod {get;set;}=18;
        public int DType {get;set;}=9;
        public int DPeriod {get;set;}=30;
        public int CombineAB {get;set;}=1;
        public int CombineBC {get;set;}=0;
        public int CombineCD {get;set;}=0;
        public int ReverseSignals {get;set;}=1;
        public int StopTicks {get;set;}=20;
        public int TargetTicks {get;set;}=32;
        public int MaxDailyEntrySubmissions {get;set;}=2;
    }
}
internal static class AdapterSmoke
{
    private static void Assert(bool v,string m){if(!v)throw new Exception(m);}
    private static NinjaTrader.NinjaScript.Parameter Par(string name,int min,int max,int inc) {
        return new NinjaTrader.NinjaScript.Parameter{Name=name,Min=min,Max=max,
            Increment=inc,Value=min};
    }
    public static int Main() {
        var s=new NQNativeGeneticLabV3();
        s.OptimizationParameters.Add(Par("Condition count (1..4)",2,4,1));
        var opt=new NinjaTrader.NinjaScript.Optimizers.NQNativeUniqueOptimizerV4();
        opt.Simulate(s,3,20261102,100);
        Assert(opt.Executed==1,
          "Only Count=2 is admissible when A=C and BC=AND, CD=AND");
        Assert(opt.Ids.Count==1,"Only one runtime identity");
        Assert(NinjaTrader.Code.Output.Logs.Any(x=>x.Contains("exhausted=True")),
          "Search must report exhausted instead of claiming 3 unique");

        // More degrees of freedom: 20 actual unique backtests, no duplicates.
        var many=new NQNativeGeneticLabV3();
        many.OptimizationParameters.Add(Par("Condition count (1..4)",1,4,1));
        many.OptimizationParameters.Add(Par("A type (0..9)",0,9,1));
        many.OptimizationParameters.Add(Par("A period",6,30,6));
        many.OptimizationParameters.Add(Par("B type (0..9)",0,9,1));
        many.OptimizationParameters.Add(Par("B period",6,30,6));
        var opt2=new NinjaTrader.NinjaScript.Optimizers.NQNativeUniqueOptimizerV4();
        opt2.Simulate(many,20,20261102,2000);
        Assert(opt2.Executed==20,"Need 20 non-repeated backtests");
        Assert(opt2.Ids.Count==20,"No duplicated runtime identity");

        // Unsupported Parameter API: the optimizer must never invoke a
        // backtest with guesses or stale strategy property values.
        var broken=new NQNativeGeneticLabV3();
        broken.OptimizationParameters.Add(new {
            Name="ConditionCount",Min=2,Max=4,Increment=1,
            Value=2 // anonymous property read-only
        });
        var opt3=new NinjaTrader.NinjaScript.Optimizers.NQNativeUniqueOptimizerV4();
        opt3.Simulate(broken,2,20261102,10);
        Assert(opt3.Executed==0,"Read-only parameter FAIL CLOSED");
        Assert(NinjaTrader.Code.Output.Logs.Any(x=>
            x.Contains("STOP binding validation")),
            "Missing user-visible warning for ABI mismatch");

        Console.WriteLine("NQ_S054_V4_NT8_ADAPTER_SHIM_TESTS_PASSED=3");
        Console.WriteLine("NQ_V4_REAL_NINJATRADER_ABI_COMPILE_NOT_VERIFIED");
        return 0;
    }
}
