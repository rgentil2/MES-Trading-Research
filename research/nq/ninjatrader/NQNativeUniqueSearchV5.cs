// S0.58 - Independent V5 C# search of 20 genes and V5 ATR exit canonical identities.
// Pure C# generator, uses original V3 Boolean canonicalizer through V5 exit helper.
// Dedup operates over V5 runtime keys including only relevant ATR exit inputs.
// It excludes internally redundant Boolean structures and all repeat fingerprints.
// Evaluated identities are counted ONLY after successful RunIteration in the
// native optimizer adapter. Generation does NOT prove profitable backtests.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQGeneRangeV5
    {
        public readonly int Min;
        public readonly int Max;
        public readonly int Step;

        public NQGeneRangeV5(int min, int max, int step)
        {
            if (min > max || step < 1 || (long)max - (long)min > Int32.MaxValue)
                throw new ArgumentException("Invalid optimizer gene domain");
            Min = min; Max = max; Step = step;
        }

        public int Count { get { return 1 + (Max - Min) / Step; } }

        public int At(int index)
        {
            if (index < 0 || index >= Count)
                throw new ArgumentOutOfRangeException("index");
            return Min + index * Step;
        }
    }

    public sealed class NQGenomeV5
    {
        public readonly int[] Genes;
        public readonly NQExitIdentityV5 Canonical;

        public NQGenomeV5(int[] genes, NQExitIdentityV5 canonical)
        {
            Genes = (int[]) genes.Clone(); Canonical = canonical;
        }
    }

    public sealed class NQUniqueSearchV5
    {
        public static readonly string[] Names = new string[] {
            "ConditionCount", "AType", "APeriod", "BType", "BPeriod",
            "CType", "CPeriod", "DType", "DPeriod",
            "CombineAB", "CombineBC", "CombineCD", "ReverseSignals",
            "StopTicks", "TargetTicks", "MaxDailyEntrySubmissions",
            "ExitMode", "ATRPeriod", "ATRStopX10", "ATRTargetX10"
        };

        private readonly NQGeneRangeV5[] ranges;
        private readonly Random random;
        private readonly HashSet<string> seen = new HashSet<string>(StringComparer.Ordinal);
        private readonly int[] scratch = new int[20];

        public int Attempted { get; private set; }
        public int GeneratedUnique { get; private set; }
        public int RedundantSkipped { get; private set; }
        public int DuplicateSkipped { get; private set; }
        public int InvalidSkipped { get; private set; }

        public NQUniqueSearchV5(NQGeneRangeV5[] ranges, int seed)
        {
            if (ranges == null || ranges.Length != Names.Length ||
                ranges.Any(x => x == null))
                throw new ArgumentException("V5 needs precisely 20 gene ranges");
            this.ranges = (NQGeneRangeV5[])ranges.Clone();
            random = new Random(seed);
        }

        public NQGenomeV5 TryNext()
        {
            Attempted++;
            for (int i = 0; i < ranges.Length; i++)
                scratch[i] = ranges[i].At(random.Next(ranges[i].Count));

            NQExitIdentityV5 c;
            try
            {
                c = NQNativeExitCanonicalV5.Analyze(scratch);
            }
            catch (ArgumentException)
            {
                InvalidSkipped++;
                return null;
            }

            if (c.IsRedundant)
            {
                RedundantSkipped++;
                return null;
            }
            if (!seen.Add(c.RuntimeKey))
            {
                DuplicateSkipped++;
                return null;
            }

            GeneratedUnique++;
            return new NQGenomeV5(scratch, c);
        }

        public static NQGeneRangeV5 Fixed(int v)
        {
            return new NQGeneRangeV5(v,v,1);
        }

        // Default for constrained structural smoke. Change in Strategy
        // Analyzer per user's explicit ranges when V5 is compiled/validated.
        public static NQGeneRangeV5[] Smoke()
        {
            return new NQGeneRangeV5[] {
                new NQGeneRangeV5(1,4,1),
                new NQGeneRangeV5(0,9,1),
                new NQGeneRangeV5(6,30,6),
                new NQGeneRangeV5(0,9,1),
                new NQGeneRangeV5(6,30,6),
                new NQGeneRangeV5(0,9,1),
                new NQGeneRangeV5(6,30,6),
                new NQGeneRangeV5(0,9,1),
                new NQGeneRangeV5(6,30,6),
                new NQGeneRangeV5(0,1,1),
                new NQGeneRangeV5(0,1,1),
                new NQGeneRangeV5(0,1,1),
                new NQGeneRangeV5(0,1,1),
                Fixed(20),Fixed(32),Fixed(2),
                new NQGeneRangeV5(0,3,1),
                Fixed(14),Fixed(15),Fixed(25)
            };
        }

        public static NQExitIdentityV5 AnalyzeGenes(int[] g)
        {
            return NQNativeExitCanonicalV5.Analyze(g);
        }
    }
}
