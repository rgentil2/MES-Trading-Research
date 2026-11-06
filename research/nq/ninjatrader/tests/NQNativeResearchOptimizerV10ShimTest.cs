// V10 CI-only NinjaTrader API shim; NOT native NinjaTrader assembly proof.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

namespace NinjaTrader.Cbi { public enum PrintTo { OutputTab1, OutputTab2 } }
namespace NinjaTrader.Code {
    public static class Output {
        public static readonly List<string> Logs=new List<string>();
        public static void Process(string s,NinjaTrader.Cbi.PrintTo t){Logs.Add(s);}
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
        public List<object> OptimizationParameters {get;set;}=new List<object>();
    }
    public abstract class Optimizer {
        protected State State {get;set;}
        protected List<StrategyBase> Strategies {get;set;}=new List<StrategyBase>();
        protected string Name {get;set;}
        protected int NumberOfIterations {get;set;}
        public readonly List<string> Ids=new List<string>();
        public int Executed {get;private set;}
        protected virtual void OnStateChange(){}
        protected abstract void OnOptimize();
        protected void RunIteration() {
            var s=(NQNativeGeneticLabV5)Strategies[0];
            int[] genes=NQUniqueSearchV5.Names.Select(
                n=>(int)s.GetType().GetProperty(n).GetValue(s,null)).ToArray();
            NQExitIdentityV5 id=NQUniqueSearchV5.AnalyzeGenes(genes);
            if(id.IsRedundant || Ids.Contains(id.RuntimeKey))
                throw new Exception("RunIteration duplicate/redundant");
            foreach(Parameter p in s.OptimizationParameters.OfType<Parameter>()) {
                int k=Array.IndexOf(NQUniqueSearchV5.Names,p.Name);
                if(k>=0 && p.Value!=genes[k])
                    throw new Exception("NT8 Parameter/Strategy desync "+p.Name);
            }
            Ids.Add(id.RuntimeKey);Executed++;
        }
        public void Simulate(NQNativeGeneticLabV5 strategy,int wanted,int seed,
                             int maxAttempts,bool explore) {
            State=State.SetDefaults;OnStateChange();
            Strategies.Add(strategy);
            var t=GetType();
            t.GetProperty("UniqueCandidates").SetValue(this,wanted,null);
            t.GetProperty("Seed").SetValue(this,seed,null);
            t.GetProperty("MaxAttempts").SetValue(this,maxAttempts,null);
            t.GetProperty("ExploreExits").SetValue(this,explore,null);
            State=State.Configure;OnStateChange();
            OnOptimize();
        }
    }
}
namespace NinjaTrader.NinjaScript.Strategies {
    public class NQNativeGeneticLabV5:NinjaTrader.NinjaScript.StrategyBase {
        public int ConditionCount {get;set;}=2;
        public int AType {get;set;}=0;
        public int APeriod {get;set;}=12;
        public int BType {get;set;}=7;
        public int BPeriod {get;set;}=14;
        public int CType {get;set;}=4;
        public int CPeriod {get;set;}=18;
        public int DType {get;set;}=6;
        public int DPeriod {get;set;}=20;
        public int CombineAB {get;set;}=0;
        public int CombineBC {get;set;}=0;
        public int CombineCD {get;set;}=0;
        public int ReverseSignals {get;set;}=0;
        public int StopTicks {get;set;}=20;
        public int TargetTicks {get;set;}=32;
        public int MaxDailyEntrySubmissions {get;set;}=2;
        public int ExitMode {get;set;}=0;
        public int ATRPeriod {get;set;}=14;
        public int ATRStopX10 {get;set;}=15;
        public int ATRTargetX10 {get;set;}=25;
    }
}
internal static class V10ShimTest {
    private static void T(bool b,string reason){if(!b)throw new Exception(reason);}
    private static NQNativeGeneticLabV5 Filled() {
        var s=new NQNativeGeneticLabV5();
        foreach(string name in NQUniqueSearchV5.Names) {
            int v=(int)s.GetType().GetProperty(name).GetValue(s,null);
            // Intentional fixed GUI ranges, historically V8 produced 1 candidate.
            s.OptimizationParameters.Add(new NinjaTrader.NinjaScript.Parameter{
                Name=name,Min=v,Max=v,Increment=1,Value=v
            });
        }
        return s;
    }
    public static int Main(){
        var s=Filled();
        int[] before=NQUniqueSearchV5.Names.Select(
            name=>(int)s.GetType().GetProperty(name).GetValue(s,null)).ToArray();
        var o=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV10();
        o.Simulate(s,200,20261105,20000,true);
        T(o.Executed==200,"fixed UI ranges must yield 200 unique runs");
        T(o.Ids.Count==200,"unique runtime canonical keys");
        T(NinjaTrader.Code.Output.Logs.Any(x=>x.Contains("RANGES=INTERNAL_GUI_MINMAX_IGNORED")),
            "must state explicit override of GUI ranges");
        for(int i=0;i<20;i++) {
            string name=NQUniqueSearchV5.Names[i];
            int value=(int)s.GetType().GetProperty(name).GetValue(s,null);
            var p=(NinjaTrader.NinjaScript.Parameter)s.OptimizationParameters[i];
            T(value==before[i] && p.Value==before[i],"restoration "+name);
        }
        // Missing parameter bindings should fail closed before RunIteration.
        var missing=Filled();missing.OptimizationParameters.RemoveAt(19);
        var bad=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV10();
        bad.Simulate(missing,20,20261105,2000,true);
        T(bad.Executed==0,"all 20 params required");

        // Reproducibility by seed.
        var second=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV10();
        second.Simulate(Filled(),200,20261105,20000,true);
        T(second.Ids.SequenceEqual(o.Ids),"deterministic 200 candidates");
        Console.WriteLine("NQ_V10_SOURCE_SHIM_PASS=200_UNIQUE_REPLAY_AND_GUARDS");
        Console.WriteLine("REAL_NT8_WINDOWS_COMPILE_AND_BACKTEST_NOT_VERIFIED");
        return 0;
    }
}
