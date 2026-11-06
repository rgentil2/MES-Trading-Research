// S0.72 — pure C# fitness-guided NQ evolutionary research engine.
// NOT a NinjaTrader fill engine and NOT a claim of profitable strategies.
// The fitness callback must be backed by HISTORICAL 2020-22 scoring before
// V12 can rank actual NQ strategies; tests use explicitly synthetic fitness.
// 20 V11 integer genes; 132 condition catalog; versioned Boolean/exit
// signatures; global dedup; elitism, tournament, paired-leaf crossover,
// mutational search, immigrants and stagnation reset. No OOS input.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQEvolutionConfigV12
    {
        public int Population = 64;
        public int Generations = 12;
        public int Elites = 6;
        public int Tournament = 4;
        public int ImmigrantPercent = 20;
        public int MutationPercent = 18;
        public int Seed = 20261105;
        public int MaxAttempts = 200000;
        public int ResetAfterStagnantGenerations = 4;

        public void Validate()
        {
            if(Population<8||Population>10000||
               Generations<1||Generations>10000||
               Elites<1||Elites>=Population||
               Tournament<2||Tournament>Population||
               ImmigrantPercent<0||ImmigrantPercent>90||
               MutationPercent<1||MutationPercent>100||
               Seed<1||MaxAttempts<Population||
               ResetAfterStagnantGenerations<1)
                throw new ArgumentException("Invalid V12 GA configuration");
        }
    }

    public sealed class NQEvolutionIndividualV12
    {
        public readonly NQGenomeV11 Genome;
        public readonly double Score;
        public readonly int BirthGeneration;
        public readonly string Source;
        public NQEvolutionIndividualV12(NQGenomeV11 genome,double score,
                                       int generation,string source)
        { Genome=genome;Score=score;BirthGeneration=generation;Source=source; }
    }

    public sealed class NQEvolutionSummaryV12
    {
        public readonly List<NQEvolutionIndividualV12> Evaluated =
            new List<NQEvolutionIndividualV12>();
        public readonly List<double> GenerationBest = new List<double>();
        public readonly List<int> GenerationNew = new List<int>();
        public NQEvolutionIndividualV12 Best;
        public int Attempts,Duplicates,Invalid,Redundant,InvalidFitness;
        public int CrossoverChildren,MutatedChildren,ImmigrantChildren,Resets;
        public int IncompleteGenerations;
    }

    public sealed class NQEvolutionEngineV12
    {
        private readonly NQGeneRangeV11[] ranges;
        private readonly NQEvolutionConfigV12 cfg;
        private readonly Random rng;
        private readonly HashSet<string> evaluated =
            new HashSet<string>(StringComparer.Ordinal);
        private readonly NQEvolutionSummaryV12 summary =
            new NQEvolutionSummaryV12();

        private static readonly int[][] CrossoverGroups = {
            new[]{0}, new[]{1,2}, new[]{3,4}, new[]{5,6},
            new[]{7,8}, new[]{9,10,11,12}, new[]{13,14,15,16,17,18,19}
        };

        public NQEvolutionEngineV12(NQGeneRangeV11[] searchRanges,
                                    NQEvolutionConfigV12 settings)
        {
            if(searchRanges==null||searchRanges.Length!=20||
               searchRanges.Any(x=>x==null)||settings==null)
                throw new ArgumentException("20 V11 search domains and GA config required");
            settings.Validate();
            ranges=(NQGeneRangeV11[])searchRanges.Clone();
            cfg=settings;
            rng=new Random(settings.Seed);
        }

        private int[] RandomGenes()
        {
            var g=new int[20];
            for(int i=0;i<20;i++)g[i]=ranges[i].At(rng.Next(ranges[i].Count));
            return g;
        }

        private NQEvolutionIndividualV12 Tournament(
            List<NQEvolutionIndividualV12> population)
        {
            NQEvolutionIndividualV12 winner=null;
            for(int i=0;i<cfg.Tournament;i++)
            {
                var competitor=population[rng.Next(population.Count)];
                if(winner==null||competitor.Score>winner.Score)
                    winner=competitor;
            }
            return winner;
        }

        private int[] Breed(List<NQEvolutionIndividualV12> parents,
                            bool forceImmigrant,out string kind)
        {
            if(forceImmigrant)
            {
                summary.ImmigrantChildren++;
                kind="IMMIGRANT";
                return RandomGenes();
            }
            int[] left=Tournament(parents).Genome.Genes;
            int[] right=Tournament(parents).Genome.Genes;
            int[] child=(int[])left.Clone();
            // Crossover preserves the identity of each (indicator,period)
            // leaf; avoids splicing a period from an unrelated parent.
            if(rng.Next(100)<88)
            {
                bool switched=false;
                foreach(int[] group in CrossoverGroups)
                {
                    if(rng.Next(2)==0)continue;
                    foreach(int i in group)child[i]=right[i];
                    switched=true;
                }
                if(switched)summary.CrossoverChildren++;
            }
            bool mutated=false;
            for(int i=0;i<20;i++)
            {
                if(ranges[i].Count<=1||rng.Next(100)>=cfg.MutationPercent)
                    continue;
                int old=child[i],next=old;
                // Half small local moves and half global jumps.
                if(rng.Next(2)==0)
                {
                    int index=(old-ranges[i].Min)/ranges[i].Step;
                    int delta=rng.Next(2)==0?-1:1;
                    index=Math.Max(0,Math.Min(ranges[i].Count-1,index+delta));
                    next=ranges[i].At(index);
                }
                else
                    next=ranges[i].At(rng.Next(ranges[i].Count));
                if(next!=old){child[i]=next;mutated=true;}
            }
            if(mutated)summary.MutatedChildren++;
            kind=mutated?"MUTANT":"CROSSOVER";
            return child;
        }

        private NQEvolutionIndividualV12 EvaluateUnique(
            int[] g,int generation,string source,
            Func<NQGenomeV11,double> fitness)
        {
            summary.Attempts++;
            NQExitIdentityV11 identity;
            try { identity=NQNativeExitCanonicalV11.Analyze(g); }
            catch(ArgumentException){summary.Invalid++;return null;}
            if(identity.IsRedundant){summary.Redundant++;return null;}
            if(!evaluated.Add(identity.RuntimeKey)){summary.Duplicates++;return null;}
            var genome=new NQGenomeV11(g,identity);
            double score;
            try {score=fitness(genome);}
            catch(Exception){summary.InvalidFitness++;score=-1.0e12;}
            if(Double.IsNaN(score)||Double.IsInfinity(score))
            {
                score=-1.0e12;
                summary.InvalidFitness++;
            }
            var one=new NQEvolutionIndividualV12(genome,score,
                                                  generation,source);
            summary.Evaluated.Add(one);
            if(summary.Best==null||score>summary.Best.Score)
                summary.Best=one;
            return one;
        }

        public NQEvolutionSummaryV12 Run(Func<NQGenomeV11,double> fitness)
        {
            if(fitness==null)throw new ArgumentNullException("fitness");
            // Single-run semantics: no accidental reuse of evaluated keys.
            if(summary.Attempts>0)
                throw new InvalidOperationException("Create a new V12 engine per run");
            var parents=new List<NQEvolutionIndividualV12>();
            int stalled=0;
            double previousBest=Double.NegativeInfinity;
            for(int gen=0;gen<cfg.Generations;gen++)
            {
                var cohort=new List<NQEvolutionIndividualV12>();
                int elites=gen==0?0:Math.Min(cfg.Elites,parents.Count);
                if(gen>0)
                {
                    var survivors=parents.OrderByDescending(x=>x.Score)
                        .ThenBy(x=>x.Genome.Canonical.RuntimeKey,
                                StringComparer.Ordinal)
                        .Take(elites).ToList();
                    cohort.AddRange(survivors); // already scored, no re-test
                }
                int births=0;
                while(cohort.Count<cfg.Population &&
                      summary.Attempts<cfg.MaxAttempts)
                {
                    bool restart=gen>0 &&
                        stalled>=cfg.ResetAfterStagnantGenerations;
                    bool immigrant=gen==0||restart||
                        rng.Next(100)<cfg.ImmigrantPercent;
                    string kind;
                    int[] child=immigrant||parents.Count==0?RandomGenes():
                        Breed(parents,false,out kind);
                    if(immigrant)
                    {
                        summary.ImmigrantChildren++;
                        kind="IMMIGRANT";
                    }
                    else kind="EVOLVED";
                    var evaluatedChild=EvaluateUnique(child,gen,kind,fitness);
                    if(evaluatedChild==null)continue;
                    cohort.Add(evaluatedChild);births++;
                }
                if(cohort.Count<cfg.Population)summary.IncompleteGenerations++;
                if(cohort.Count==0)break;
                parents=cohort.OrderByDescending(x=>x.Score)
                    .ThenBy(x=>x.Genome.Canonical.RuntimeKey,
                            StringComparer.Ordinal).ToList();
                summary.GenerationBest.Add(summary.Best.Score);
                summary.GenerationNew.Add(births);
                if(summary.Best.Score>previousBest+1e-9)
                {
                    previousBest=summary.Best.Score;
                    stalled=0;
                }
                else stalled++;
                if(stalled>=cfg.ResetAfterStagnantGenerations)
                {
                    summary.Resets++;
                    // Next cohort keeps elite survivors; fills the remaining
                    // slots with immigrants. Do not erase best ever.
                }
                if(summary.Attempts>=cfg.MaxAttempts)break;
            }
            return summary;
        }
    }
}
