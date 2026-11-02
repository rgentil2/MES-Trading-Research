// S0.54 - NinjaTrader 8 Custom Optimizer V4, initial fail-closed adapter.
// Generates C# V3 semantic unique genomes *before* RunIteration().
// Requires strategy NQNativeGeneticLabV3 and custom fitness V3.
// It is not an evolutionary genetic algorithm yet: deterministic seeded
// RANDOM structural discovery with canonical dedup and exact NT8 backtest.
// Mutation/crossover and 132 indicator routes are future steps.
//
// The public NinjaTrader documentation guarantees OnOptimize, Strategies[0]
// .OptimizationParameters and RunIteration, but omits the concrete Parameter
// range/value mutator contract. This adapter discovers the installed Parameter
// object's metadata via reflection, fails closed if any required member is
// absent, and NEVER falls back to using stale/default values for a backtest.
// This version must be compiled and checked in the user's installed NT8.
//
// V1/V2/V3 and historical source untouched. 2020..2022 only enforced by V3.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.Linq;
using System.Reflection;
using NinjaTrader.NinjaScript;
using NinjaTrader.Cbi;
using NinjaTrader.NinjaScript.Strategies;

namespace NinjaTrader.NinjaScript.Optimizers
{
    public class NQNativeUniqueOptimizerV4 : Optimizer
    {
        [NinjaScriptProperty]
        [Display(Name="Unique candidates target (smoke 20)",Order=1,GroupName="01 V4")]
        [Range(1,10000)]
        public int UniqueCandidates { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Random seed",Order=2,GroupName="01 V4")]
        [Range(1,Int32.MaxValue)]
        public int Seed { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Max attempts",Order=3,GroupName="01 V4")]
        [Range(1,2000000)]
        public int MaxAttempts { get; set; }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "NQNativeUniqueOptimizerV4";
                UniqueCandidates = 20;
                Seed = 20261102;
                MaxAttempts = 10000;
            }
            else if (State == State.Configure && Strategies != null &&
                     Strategies.Count == 1)
            {
                NumberOfIterations = UniqueCandidates;
            }
        }

        private static void Tell(string message)
        {
            NinjaTrader.Code.Output.Process("NQ_V4 " + message,
                PrintTo.OutputTab1);
        }

        private static object ReadMember(object obj, params string[] names)
        {
            if (obj == null) return null;
            var t = obj.GetType();
            foreach (string name in names)
            {
                var p = t.GetProperty(name,BindingFlags.Public|BindingFlags.Instance);
                if (p != null && p.CanRead) return p.GetValue(obj,null);
                var f = t.GetField(name,BindingFlags.Public|BindingFlags.Instance);
                if (f != null) return f.GetValue(obj);
            }
            return null;
        }

        private static bool WriteMember(object obj, object value, params string[] names)
        {
            if (obj == null) return false;
            var t = obj.GetType();
            foreach (string name in names)
            {
                var p = t.GetProperty(name,BindingFlags.Public|BindingFlags.Instance);
                if (p != null && p.CanWrite)
                {
                    p.SetValue(obj,Convert.ChangeType(value,p.PropertyType,
                        CultureInfo.InvariantCulture),null);
                    return true;
                }
                var f = t.GetField(name,BindingFlags.Public|BindingFlags.Instance);
                if (f != null && !f.IsInitOnly)
                {
                    f.SetValue(obj,Convert.ChangeType(value,f.FieldType,
                        CultureInfo.InvariantCulture));
                    return true;
                }
            }
            return false;
        }

        private static string Description(object value)
        {
            if (value == null) return "(null)";
            var t = value.GetType();
            return t.FullName + " members=[" +
                String.Join(",",t.GetProperties(BindingFlags.Public|BindingFlags.Instance)
                  .Select(p=>p.Name).Concat(
                    t.GetFields(BindingFlags.Public|BindingFlags.Instance)
                     .Select(f=>f.Name)).ToArray()) + "]";
        }

        private static string Normalize(string s)
        {
            return new string((s??"").Where(char.IsLetterOrDigit)
                .Select(char.ToLowerInvariant).ToArray());
        }

        private static string Friendly(string n)
        {
            switch(n)
            {
                case "ConditionCount":return "Condition count (1..4)";
                case "AType":return "A type (0..9)";
                case "APeriod":return "A period";
                case "BType":return "B type (0..9)";
                case "BPeriod":return "B period";
                case "CType":return "C type (0..9)";
                case "CPeriod":return "C period";
                case "DType":return "D type (0..9)";
                case "DPeriod":return "D period";
                case "CombineAB":return "AB (AND=0 OR=1)";
                case "CombineBC":return "BC (AND=0 OR=1)";
                case "CombineCD":return "CD (AND=0 OR=1)";
                case "ReverseSignals":return "Reverse (0/1)";
                case "StopTicks":return "Stop ticks";
                case "TargetTicks":return "Target ticks (0=none)";
                case "MaxDailyEntrySubmissions":return "Max daily entry submissions";
                default:return n;
            }
        }

        private static int MatchGene(object parameter)
        {
            var candidates=new List<string>();
            foreach(string key in new[]{"Name","DisplayName","PropertyName"})
            {
                var x=ReadMember(parameter,key);
                if(x!=null)candidates.Add(Convert.ToString(x));
            }
            var property=ReadMember(parameter,"Property","PropertyInfo",
                "PropertyDescriptor");
            if(property!=null)
            {
                if(property is PropertyInfo)
                    candidates.Add(((PropertyInfo)property).Name);
                else
                {
                    var n=ReadMember(property,"Name","DisplayName");
                    if(n!=null)candidates.Add(Convert.ToString(n));
                }
            }

            for(int i=0;i<NQUniqueSearchV4.Names.Length;i++)
            {
                string n=NQUniqueSearchV4.Names[i];
                string target=Normalize(n),label=Normalize(Friendly(n));
                if(candidates.Any(s=>Normalize(s)==target ||
                                    Normalize(s)==label))
                    return i;
            }
            return -1;
        }

        private sealed class Bound
        {
            public object Parameter;
            public int Index;
            public int Min,Max,Increment;
            public object PreviousValue;
        }

        protected override void OnOptimize()
        {
            // Do not run backtests against an unexpected strategy.
            if (Strategies == null || Strategies.Count != 1 ||
                !(Strategies[0] is NQNativeGeneticLabV3))
            {
                Tell("STOP: select exactly NQNativeGeneticLabV3.");
                return;
            }
            var strategy=Strategies[0];
            if (UniqueCandidates < 1 || UniqueCandidates > 10000 ||
                MaxAttempts < 1 || MaxAttempts > 2000000 || Seed < 1)
            {
                Tell("STOP: bad target/seed/attempt guardrail.");
                return;
            }
            if (strategy.OptimizationParameters == null ||
                strategy.OptimizationParameters.Count < 1)
            {
                Tell("STOP: no optimizable parameters chosen.");
                return;
            }

            var ranges=new NQGeneRangeV4[16];
            var baseValues=new int[16];
            var properties=new PropertyInfo[16];
            var binding=new List<Bound>();
            Type t=strategy.GetType();
            try
            {
                for(int i=0;i<16;i++)
                {
                    properties[i]=t.GetProperty(NQUniqueSearchV4.Names[i],
                        BindingFlags.Public|BindingFlags.Instance);
                    if(properties[i]==null || !properties[i].CanWrite ||
                        properties[i].PropertyType!=typeof(int))
                        throw new InvalidOperationException("Missing V3 gene "+NQUniqueSearchV4.Names[i]);
                    baseValues[i]=Convert.ToInt32(properties[i].GetValue(strategy,null));
                    ranges[i]=NQUniqueSearchV4.Fixed(baseValues[i]);
                }

                foreach(var param in strategy.OptimizationParameters)
                {
                    object p=param;
                    int i=MatchGene(p);
                    if(i<0 || binding.Any(b=>b.Index==i))
                        throw new InvalidOperationException("Unknown/duplicated NT8 Parameter: "+Description(p));

                    var min=ReadMember(p,"Min","Minimum","MinValue");
                    var max=ReadMember(p,"Max","Maximum","MaxValue");
                    var step=ReadMember(p,"Increment","Step","StepSize");
                    var value=ReadMember(p,"Value","CurrentValue");
                    if(min==null || max==null || step==null || value==null)
                        throw new InvalidOperationException("NT8 Parameter range/value contract missing: "+Description(p));
                    int low=Convert.ToInt32(min),high=Convert.ToInt32(max),
                        incr=Convert.ToInt32(step);
                    ranges[i]=new NQGeneRangeV4(low,high,incr);
                    binding.Add(new Bound{Parameter=p,Index=i,
                         Min=low,Max=high,Increment=incr,PreviousValue=value});
                }
                // Verify ability to update every NT8 Parameter BEFORE the
                // first RunIteration. Zero historical tests if unsupported.
                foreach(var b in binding)
                    if(!WriteMember(b.Parameter,b.PreviousValue,
                         "Value","CurrentValue"))
                        throw new InvalidOperationException(
                          "Parameter value is read-only: "+Description(b.Parameter));
            }
            catch(Exception ex)
            {
                Tell("STOP binding validation: "+ex.Message);
                return;
            }

            var search=new NQUniqueSearchV4(ranges,Seed);
            int executed=0;
            int executionFailures=0;
            NumberOfIterations=UniqueCandidates;

            // Fail closed: NO cross-instrument, no OOS, no LIVE orders.
            Tell("BEGIN target="+UniqueCandidates+" seed="+Seed+
                 " maxAttempts="+MaxAttempts+
                 " selectedParams="+binding.Count+
                 " baseline=[16 V3 genes]");

            try
            {
                while(executed<UniqueCandidates && search.Attempted<MaxAttempts)
                {
                    var genome=search.TryNext();
                    if(genome==null)continue;
                    // Important: write both the optimizer's Parameter object
                    // and strategy object's visible gene. No silent fallback.
                    foreach(var b in binding)
                    {
                        int n=genome.Genes[b.Index];
                        if(!WriteMember(b.Parameter,n,"Value","CurrentValue"))
                            throw new InvalidOperationException(
                                "Unable to set runtime optimizer gene: "+NQUniqueSearchV4.Names[b.Index]);
                        properties[b.Index].SetValue(strategy,n,null);
                        object current=ReadMember(b.Parameter,"Value","CurrentValue");
                        if(current==null || Convert.ToInt32(current)!=n ||
                           Convert.ToInt32(properties[b.Index].GetValue(strategy,null))!=n)
                            throw new InvalidOperationException(
                                "Roundtrip mismatch on "+NQUniqueSearchV4.Names[b.Index]);
                    }

                    Tell("PRE_RUN candidate="+(executed+1)+
                        " uniqueId="+genome.Canonical.Fingerprint+
                        " effective="+genome.Canonical.EffectiveLeaves+
                        " genes="+String.Join("/",genome.Genes.Select(
                            x=>x.ToString(CultureInfo.InvariantCulture)).ToArray()));
                    RunIteration(); // ONLY AFTER the uniqueness check
                    executed++;
                }
            }
            catch(Exception ex)
            {
                executionFailures++;
                Tell("STOP iteration: "+ex.GetType().Name+" "+ex.Message);
            }
            finally
            {
                foreach(var b in binding)
                {
                    try {WriteMember(b.Parameter,b.PreviousValue,
                           "Value","CurrentValue");}
                    catch { /* avoid masking original optimizer exception */ }
                }
                Tell("END executed="+executed+
                    " generatedUnique="+search.GeneratedUnique+
                    " attempted="+search.Attempted+
                    " structuralRedundantSkipped="+search.RedundantSkipped+
                    " equivalentFingerprintSkipped="+search.DuplicateSkipped+
                    " invalidSkipped="+search.InvalidSkipped+
                    " failure="+executionFailures+
                    " exhausted="+(executed<UniqueCandidates));
            }
        }
    }
}
