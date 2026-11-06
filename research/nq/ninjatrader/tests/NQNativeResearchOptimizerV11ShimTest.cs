// V11 CI-only NinjaTrader API shim; NOT native NinjaTrader assembly proof.
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
    // Simulates a platform Parameter implementation that enforces Min/Max
    // on writes. V11 must then STOP without incorrectly claiming any backtest.
    public class StrictRangeParameter {
        public string Name {get;set;}
        public int Min {get;set;}
        public int Max {get;set;}
        public int Increment {get;set;}
        private int stored;
        public int Value {
            get {return stored;}
            set {
                if(value<Min || value>Max)
                    throw new InvalidOperationException("Outside parameter domain");
                stored=value;
            }
        }
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
        public readonly List<int[]> Genomes=new List<int[]>();
        public int Executed {get;private set;}
        protected virtual void OnStateChange(){}
        protected abstract void OnOptimize();
        protected void RunIteration() {
            var s=(NQNativeSignalLabV11)Strategies[0];
            int[] genes=NQUniqueSearchV11.Names.Select(
                n=>(int)s.GetType().GetProperty(n).GetValue(s,null)).ToArray();
            NQExitIdentityV11 id=NQUniqueSearchV11.AnalyzeGenes(genes);
            if(id.IsRedundant || Ids.Contains(id.RuntimeKey))
                throw new Exception("RunIteration duplicate/redundant");
            foreach(Parameter p in s.OptimizationParameters.OfType<Parameter>()) {
                int k=Array.IndexOf(NQUniqueSearchV11.Names,p.Name);
                if(k>=0 && p.Value!=genes[k])
                    throw new Exception("NT8 Parameter/Strategy desync "+p.Name);
            }
            Ids.Add(id.RuntimeKey);
            Genomes.Add((int[])genes.Clone());
            Executed++;
        }
        public void Simulate(NQNativeSignalLabV11 strategy,int wanted,int seed,
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
    public class NQNativeSignalLabV11:NinjaTrader.NinjaScript.StrategyBase {
        public int ConditionCount {get;set;}=2;
        public int AType {get;set;}=0;
        public int APeriod {get;set;}=12;
        public int BType {get;set;}=44;
        public int BPeriod {get;set;}=14;
        public int CType {get;set;}=77;
        public int CPeriod {get;set;}=18;
        public int DType {get;set;}=121;
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
internal static class V11ShimTest {
    private static void T(bool b,string reason){if(!b)throw new Exception(reason);}
    private static NQNativeSignalLabV11 Filled() {
        var s=new NQNativeSignalLabV11();
        foreach(string name in NQUniqueSearchV11.Names) {
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
        int[] before=NQUniqueSearchV11.Names.Select(
            name=>(int)s.GetType().GetProperty(name).GetValue(s,null)).ToArray();
        var o=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV11();
        o.Simulate(s,1000,20261105,40000,true);
        T(o.Executed==1000,"fixed UI ranges must yield 1000 unique runs");
        T(o.Ids.Count==1000,"unique runtime canonical keys");
        int[] slots={1,3,5,7};
        var visited=new HashSet<int>();
        foreach(int[] genes in o.Genomes)
            for(int slot=0;slot<genes[0];slot++)
                visited.Add(genes[slots[slot]]);
        T(visited.Count==132,"all 132 catalog types sampled in active genomes "+
            visited.Count);
        T(o.Genomes.Select(g=>g[16]).Distinct().Count()>1,
            "exploratory exit modes must actually vary");
        T(o.Genomes.Select(g=>g[13]).Distinct().Count()>1,
            "exploratory stop tick genes must actually vary");
        T(NinjaTrader.Code.Output.Logs.Any(x=>x.Contains("RANGES=INTERNAL_GUI_MINMAX_IGNORED")),
            "must state explicit override of GUI ranges");
        for(int i=0;i<20;i++) {
            string name=NQUniqueSearchV11.Names[i];
            int value=(int)s.GetType().GetProperty(name).GetValue(s,null);
            var p=(NinjaTrader.NinjaScript.Parameter)s.OptimizationParameters[i];
            T(value==before[i] && p.Value==before[i],"restoration "+name);
        }
        // Missing parameter bindings should fail closed before RunIteration.
        var missing=Filled();missing.OptimizationParameters.RemoveAt(19);
        var bad=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV11();
        bad.Simulate(missing,20,20261105,2000,true);
        T(bad.Executed==0,"all 20 params required");

        // V11 canonical namespace and distinct type identity.
        var sample=(int[])before.Clone();
        sample[0]=1;sample[1]=131;sample[2]=12;
        var upper=NQUniqueSearchV11.AnalyzeGenes(sample);
        sample[1]=0;
        var lower=NQUniqueSearchV11.AnalyzeGenes(sample);
        T(upper.RuntimeKey!=lower.RuntimeKey &&
          upper.Fingerprint.StartsWith("NQEX11_"),
          "condition 131 must be distinct and versioned");
        // Reproducibility by seed.
        var second=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV11();
        second.Simulate(Filled(),1000,20261105,40000,true);
        T(second.Ids.SequenceEqual(o.Ids),"deterministic 1000 candidates");
        // Exit-frozen mode: search structural identities without changing baseline
        // protective exit genes, despite all GUI ranges being fixed.
        var frozen=Filled();
        int[] frozenBaseline=NQUniqueSearchV11.Names.Select(
            n=>(int)frozen.GetType().GetProperty(n).GetValue(frozen,null)).ToArray();
        var frozenOpt=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV11();
        frozenOpt.Simulate(frozen,500,20261106,30000,false);
        T(frozenOpt.Executed==500,"500 exit-frozen structural candidates");
        T(frozenOpt.Ids.Count==500,"unique frozen-exit candidates");
        T(frozenOpt.Genomes.All(g=>Enumerable.Range(13,7)
            .All(i=>g[i]==frozenBaseline[i])),
            "all 500 executed genomes must hold the seven exit/risk genes");
        for(int i=13;i<20;i++) {
            string n=NQUniqueSearchV11.Names[i];
            T((int)frozen.GetType().GetProperty(n).GetValue(frozen,null)
                ==frozenBaseline[i],"frozen baseline restored "+n);
        }
        // Simulate a NinjaTrader Parameter that rejects writes outside fixed
        // Min=Max. This remains a real-NT8 runtime uncertainty, so the correct
        // behavior is fail closed, not a claimed successful optimization.
        var strict=Filled();
        for(int k=0;k<strict.OptimizationParameters.Count;k++) {
            var sp=(NinjaTrader.NinjaScript.Parameter)strict.OptimizationParameters[k];
            strict.OptimizationParameters[k]=new NinjaTrader.NinjaScript.StrictRangeParameter{
                Name=sp.Name,Min=sp.Min,Max=sp.Max,Increment=sp.Increment,
                Value=sp.Value
            };
        }
        var failsafe=new NinjaTrader.NinjaScript.Optimizers.NQNativeResearchOptimizerV11();
        failsafe.Simulate(strict,20,20261105,500,true);
        T(failsafe.Executed==0,
            "strict parameter min-max setter must fail closed before backtest");
        T(NinjaTrader.Code.Output.Logs.Any(x=>x.Contains("NQ_V11 STOP")),
            "strict min-max rejection must be recorded");
        Console.WriteLine("NQ_V11_SOURCE_SHIM_PASS=1000_UNIQUE_500_FROZEN_REPLAY_RANGES_AND_GUARDS");
        Console.WriteLine("REAL_NT8_WINDOWS_COMPILE_AND_BACKTEST_NOT_VERIFIED");
        return 0;
    }
}
