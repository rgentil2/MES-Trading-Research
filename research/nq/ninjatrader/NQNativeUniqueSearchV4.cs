// S0.54 - Exact C# source used by the independent V4 NinjaTrader optimizer.
// NO NinjaTrader dependencies. Uses V3 Boolean canonicalizer for semantic IDs.
// "unique" means unique per V3 runtime fingerprint for fixed market/dataset/costs.
// It excludes internally redundant Boolean structures and all repeat fingerprints.
// Evaluated identities are counted ONLY after successful RunIteration in the
// native optimizer adapter. Unique generation is NOT historical trade success.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQGeneRangeV4
    {
        public readonly int Min;
        public readonly int Max;
        public readonly int Step;

        public NQGeneRangeV4(int min, int max, int step)
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

    public sealed class NQGenomeV4
    {
        public readonly int[] Genes;
        public readonly NQCanonicalResultV3 Canonical;

        public NQGenomeV4(int[] genes, NQCanonicalResultV3 canonical)
        {
            Genes = (int[]) genes.Clone(); Canonical = canonical;
        }
    }

    public sealed class NQUniqueSearchV4
    {
        public static readonly string[] Names = new string[] {
            "ConditionCount", "AType", "APeriod", "BType", "BPeriod",
            "CType", "CPeriod", "DType", "DPeriod",
            "CombineAB", "CombineBC", "CombineCD", "ReverseSignals",
            "StopTicks", "TargetTicks", "MaxDailyEntrySubmissions"
        };

        private readonly NQGeneRangeV4[] ranges;
        private readonly Random random;
        private readonly HashSet<string> seen = new HashSet<string>(StringComparer.Ordinal);
        private readonly int[] scratch = new int[16];

        public int Attempted { get; private set; }
        public int GeneratedUnique { get; private set; }
        public int RedundantSkipped { get; private set; }
        public int DuplicateSkipped { get; private set; }
        public int InvalidSkipped { get; private set; }

        public NQUniqueSearchV4(NQGeneRangeV4[] ranges, int seed)
        {
            if (ranges == null || ranges.Length != Names.Length ||
                ranges.Any(x => x == null))
                throw new ArgumentException("V4 needs precisely 16 gene ranges");
            this.ranges = (NQGeneRangeV4[])ranges.Clone();
            random = new Random(seed);
        }

        public NQGenomeV4 TryNext()
        {
            Attempted++;
            for (int i = 0; i < ranges.Length; i++)
                scratch[i] = ranges[i].At(random.Next(ranges[i].Count));

            NQCanonicalResultV3 c;
            try
            {
                c = NQNativeBooleanCanonicalV3.Analyze(scratch[0],
                    new[] { scratch[1], scratch[3], scratch[5], scratch[7] },
                    new[] { scratch[2], scratch[4], scratch[6], scratch[8] },
                    new[] { scratch[9], scratch[10], scratch[11] },
                    scratch[12], scratch[13], scratch[14], scratch[15]);
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
            return new NQGenomeV4(scratch, c);
        }

        public static NQGeneRangeV4 Fixed(int v)
        {
            return new NQGeneRangeV4(v,v,1);
        }

        // Default for constrained structural smoke. Change in Strategy
        // Analyzer per user's explicit ranges when V4 is compiled/validated.
        public static NQGeneRangeV4[] Smoke()
        {
            return new NQGeneRangeV4[] {
                new NQGeneRangeV4(1,4,1),
                new NQGeneRangeV4(0,9,1),
                new NQGeneRangeV4(6,30,6),
                new NQGeneRangeV4(0,9,1),
                new NQGeneRangeV4(6,30,6),
                new NQGeneRangeV4(0,9,1),
                new NQGeneRangeV4(6,30,6),
                new NQGeneRangeV4(0,9,1),
                new NQGeneRangeV4(6,30,6),
                new NQGeneRangeV4(0,1,1),
                new NQGeneRangeV4(0,1,1),
                new NQGeneRangeV4(0,1,1),
                new NQGeneRangeV4(0,1,1),
                Fixed(20),Fixed(32),Fixed(2)
            };
        }

        public static NQCanonicalResultV3 AnalyzeGenes(int[] g)
        {
            if (g == null || g.Length != 16)
                throw new ArgumentException("Need 16 genes");
            return NQNativeBooleanCanonicalV3.Analyze(g[0],
                new[] {g[1],g[3],g[5],g[7]},
                new[] {g[2],g[4],g[6],g[8]},
                new[] {g[9],g[10],g[11]},
                g[12],g[13],g[14],g[15]);
        }
    }
}
