// S0.70 - NQ research discovery optimizer V10.
// Native NT8 historical Strategy Analyzer only, NEVER deploy live.
// Purpose: avoid accidental Min=Max genetic exhaustion by owning the
// discovery domains here, while retaining existing V5 execution + dedup.
// Uses NQUniqueSearchV5, NQNativeExitCanonicalV5 and V5/V8 strategies.
// Candidate scoring is selected separately: NQNativeDiscoveryFitnessV9.
// This is seeded broad random structural search, NOT fitness-guided GA,
// arbitrary rule trees, a 132-indicator catalog or StrategyQuant parity.
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.Linq;
using System.Reflection;
using NinjaTrader.Cbi;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;

namespace NinjaTrader.NinjaScript.Optimizers
{
    public class NQNativeResearchOptimizerV10 : Optimizer
    {
        [NinjaScriptProperty]
        [Range(1, 10000)]
        [Display(Name="Unique historical candidates",Order=1,GroupName="V10 Discovery")]
        public int UniqueCandidates { get; set; }

        [NinjaScriptProperty]
        [Range(1, Int32.MaxValue)]
        [Display(Name="Reproducible seed",Order=2,GroupName="V10 Discovery")]
        public int Seed { get; set; }

        [NinjaScriptProperty]
        [Range(1, 2000000)]
        [Display(Name="Maximum generation attempts",Order=3,GroupName="V10 Discovery")]
        public int MaxAttempts { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Explore protective exits",Order=4,GroupName="V10 Discovery")]
        public bool ExploreExits { get; set; }

        private sealed class Binding
        {
            public object Parameter;
            public PropertyInfo StrategyProperty;
            public int Index;
            public object OldParameterValue;
            public int OldStrategyValue;
        }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "NQNativeResearchOptimizerV10";
                UniqueCandidates = 200;
                Seed = 20261105;
                MaxAttempts = 20000;
                ExploreExits = true;
            }
            else if (State == State.Configure && Strategies != null &&
                     Strategies.Count == 1)
                NumberOfIterations = UniqueCandidates;
        }

        private static void Log(string s)
        {
            NinjaTrader.Code.Output.Process("NQ_V10 " + s, PrintTo.OutputTab1);
        }

        private static object Read(object o, params string[] names)
        {
            if (o == null) return null;
            Type t = o.GetType();
            foreach (string n in names)
            {
                PropertyInfo p = t.GetProperty(n,BindingFlags.Public|BindingFlags.Instance);
                if (p != null && p.CanRead) return p.GetValue(o,null);
                FieldInfo f = t.GetField(n,BindingFlags.Public|BindingFlags.Instance);
                if (f != null) return f.GetValue(o);
            }
            return null;
        }

        private static bool Write(object o, object value, params string[] names)
        {
            if (o == null) return false;
            Type t = o.GetType();
            foreach (string n in names)
            {
                PropertyInfo p = t.GetProperty(n,BindingFlags.Public|BindingFlags.Instance);
                if (p != null && p.CanWrite)
                {
                    p.SetValue(o,Convert.ChangeType(value,p.PropertyType,CultureInfo.InvariantCulture),null);
                    return true;
                }
                FieldInfo f = t.GetField(n,BindingFlags.Public|BindingFlags.Instance);
                if (f != null && !f.IsInitOnly)
                {
                    f.SetValue(o,Convert.ChangeType(value,f.FieldType,CultureInfo.InvariantCulture));
                    return true;
                }
            }
            return false;
        }

        private static string Norm(string s)
        {
            return new string((s??"").Where(char.IsLetterOrDigit)
                .Select(char.ToLowerInvariant).ToArray());
        }

        private static readonly string[] UserLabels = {
            "Condition count (1..4)", "A type (0..9)", "A period",
            "B type (0..9)", "B period", "C type (0..9)", "C period",
            "D type (0..9)", "D period", "AB (AND=0 OR=1)",
            "BC (AND=0 OR=1)", "CD (AND=0 OR=1)",
            "Reverse (0/1)", "Stop ticks", "Target ticks (0=none)",
            "Max daily entry submissions", "Exit mode (0..3)",
            "ATR period", "ATR stop x10", "ATR target x10"
        };

        private static int Match(object parameter)
        {
            var aliases = new List<string>();
            foreach (string key in new[]{"Name","DisplayName","PropertyName"})
            {
                object v=Read(parameter,key);
                if(v!=null) aliases.Add(Convert.ToString(v,CultureInfo.InvariantCulture));
            }
            object prop=Read(parameter,"Property","PropertyInfo","PropertyDescriptor");
            if(prop is PropertyInfo)
                aliases.Add(((PropertyInfo)prop).Name);
            else if(prop!=null)
            {
                object n=Read(prop,"Name","DisplayName");
                if(n!=null) aliases.Add(Convert.ToString(n,CultureInfo.InvariantCulture));
            }
            for(int i=0;i<NQUniqueSearchV5.Names.Length;i++)
                if(aliases.Any(a=>Norm(a)==Norm(NQUniqueSearchV5.Names[i]) ||
                                  Norm(a)==Norm(UserLabels[i])))
                    return i;
            return -1;
        }

        private static NQGeneRangeV5 R(int lo,int hi,int step)
        { return new NQGeneRangeV5(lo,hi,step); }

        // Explicit research domains, never inferred from Min=Max GUI ranges.
        // Limits remain within V5's currently validated parameter guards.
        private static NQGeneRangeV5[] Domains(int[] baseline,bool exits)
        {
            var result=new NQGeneRangeV5[] {
                R(1,4,1), R(0,9,1), R(6,42,6),
                R(0,9,1), R(6,42,6),
                R(0,9,1), R(6,42,6),
                R(0,9,1), R(6,42,6),
                R(0,1,1), R(0,1,1), R(0,1,1), R(0,1,1),
                R(12,50,2), R(16,96,4), R(1,2,1),
                R(0,3,1), R(7,28,7), R(10,30,5), R(10,50,5)
            };
            if (!exits)
                for(int i=13;i<result.Length;i++)
                    result[i]=R(baseline[i],baseline[i],1);
            return result;
        }

        protected override void OnOptimize()
        {
            if(Strategies==null || Strategies.Count!=1 ||
               !(Strategies[0] is NQNativeGeneticLabV5))
            {
                Log("STOP requires V5 or its V8 audit subclass.");
                return;
            }
            if(UniqueCandidates<1 || UniqueCandidates>10000 ||
               MaxAttempts<1 || MaxAttempts>2000000 || Seed<1)
            {
                Log("STOP invalid V10 settings.");
                return;
            }
            var strategy=Strategies[0];
            var binding=new Binding[20];
            var original=new int[20];
            int completed=0,failed=0;
            try
            {
                // All 20 parameters must be selected, but their GUI min/max
                // MAY be equal: the V10 ranges override them deliberately.
                for(int i=0;i<20;i++)
                {
                    PropertyInfo p=strategy.GetType().GetProperty(
                        NQUniqueSearchV5.Names[i],
                        BindingFlags.Public|BindingFlags.Instance);
                    if(p==null || !p.CanRead || !p.CanWrite ||
                       p.PropertyType!=typeof(int))
                        throw new InvalidOperationException(
                            "Missing 20-gene V5 property "+NQUniqueSearchV5.Names[i]);
                    original[i]=Convert.ToInt32(p.GetValue(strategy,null));
                    binding[i]=new Binding{
                        StrategyProperty=p,Index=i,
                        OldStrategyValue=original[i]
                    };
                }
                if(strategy.OptimizationParameters==null ||
                   strategy.OptimizationParameters.Count!=20)
                    throw new InvalidOperationException(
                        "Select ALL 20 V5 strategy parameters for optimization. "+
                        "Their min/max may remain fixed because V10 uses internal ranges.");
                var seen=new HashSet<int>();
                foreach(var parameter in strategy.OptimizationParameters)
                {
                    int index=Match(parameter);
                    if(index<0 || !seen.Add(index))
                        throw new InvalidOperationException(
                            "Unknown or duplicate strategy optimizer parameter.");
                    object old=Read(parameter,"Value","CurrentValue");
                    if(old==null || !Write(parameter,old,"Value","CurrentValue"))
                        throw new InvalidOperationException(
                            "Runtime parameter Value cannot be written: "+
                            NQUniqueSearchV5.Names[index]);
                    binding[index].Parameter=parameter;
                    binding[index].OldParameterValue=old;
                }
                if(seen.Count!=20)
                    throw new InvalidOperationException("Incomplete 20-gene binding.");
                NQGeneRangeV5[] ranges=Domains(original,ExploreExits);
                var search=new NQUniqueSearchV5(ranges,Seed);
                NumberOfIterations=UniqueCandidates;
                Log("BEGIN target="+UniqueCandidates+" seed="+Seed+
                    " maxAttempts="+MaxAttempts+" selectedGenes=20"+
                    " exploreExits="+ExploreExits+
                    " RANGES=INTERNAL_GUI_MINMAX_IGNORED"+
                    " NOTE=RESEARCH_DISCOVERY_NOT_SQX_PARITY");
                while(completed<UniqueCandidates && search.Attempted<MaxAttempts)
                {
                    NQGenomeV5 genome=search.TryNext();
                    if(genome==null)continue;
                    for(int i=0;i<binding.Length;i++)
                    {
                        Binding b=binding[i];
                        int gene=genome.Genes[i];
                        if(!Write(b.Parameter,gene,"Value","CurrentValue"))
                            throw new InvalidOperationException(
                                "Failed parameter set "+NQUniqueSearchV5.Names[i]);
                        b.StrategyProperty.SetValue(strategy,gene,null);
                        object check=Read(b.Parameter,"Value","CurrentValue");
                        if(check==null || Convert.ToInt32(check)!=gene ||
                           Convert.ToInt32(b.StrategyProperty.GetValue(strategy,null))!=gene)
                            throw new InvalidOperationException(
                                "Value roundtrip mismatch "+NQUniqueSearchV5.Names[i]);
                    }
                    Log("PRE_RUN candidate="+(completed+1)+
                        " id="+genome.Canonical.Fingerprint+
                        " effective="+genome.Canonical.EffectiveLeaves+
                        " genes="+String.Join("/",genome.Genes.Select(
                            z=>z.ToString(CultureInfo.InvariantCulture)).ToArray()));
                    RunIteration();
                    completed++;
                }
                Log("END completed="+completed+
                    " attempts="+search.Attempted+
                    " unique="+search.GeneratedUnique+
                    " redundant="+search.RedundantSkipped+
                    " duplicate="+search.DuplicateSkipped+
                    " invalid="+search.InvalidSkipped+
                    " exhausted="+(completed<UniqueCandidates));
            }
            catch(Exception ex)
            {
                failed++;
                Log("STOP "+ex.GetType().Name+" "+ex.Message);
            }
            finally
            {
                for(int i=0;i<binding.Length;i++)
                {
                    Binding b=binding[i];
                    if(b==null)continue;
                    try
                    {
                        if(b.Parameter!=null)
                            Write(b.Parameter,b.OldParameterValue,"Value","CurrentValue");
                        b.StrategyProperty.SetValue(strategy,b.OldStrategyValue,null);
                    }
                    catch(Exception restore)
                    {
                        Log("RESTORE_WARNING "+NQUniqueSearchV5.Names[i]+
                            " "+restore.Message);
                    }
                }
                Log("FINAL executed="+completed+" failures="+failed);
            }
        }
    }
}
