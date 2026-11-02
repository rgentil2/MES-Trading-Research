// S0.49 - Pure C# canonicalizer for up to four V2/V3 boolean condition slots.
// No NinjaTrader dependency: actual C# semantics tested using .NET in GitHub CI.
// A leaf identity is (indicator type, lookback period); it is considered the
// same boolean in both bullish and bearish paths only for EXACT same inputs.
// For each expression, compute the truth table of independent unique leaves,
// discard boolean-inessential leaves, and normalize variable order. This proves
// boolean equivalence (incl. A=C), NOT full trade equality: warmup can differ.
//
// IMPORTANT: every optimization run still performs a backtest in NinjaTrader's
// built-in Genetic optimizer. Canonical signatures + per-structure rejection
// do not eliminate cross-genotype backtest work or guarantee 10K unique ones.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQCanonicalResultV3
    {
        public string BooleanKey { get; internal set; }
        public string RuntimeKey { get; internal set; }
        public string Fingerprint { get; internal set; }
        public int ActiveLeaves { get; internal set; }
        public int EffectiveLeaves { get; internal set; }
        public int WarmupBars { get; internal set; }
        public bool IsRedundant { get { return EffectiveLeaves < ActiveLeaves; } }
    }

    public static class NQNativeBooleanCanonicalV3
    {
        private static string LeafKey(int type, int period)
        {
            return type.ToString("D2") + ":" + period.ToString("D3");
        }

        // op == 0 means AND; op == 1 means OR. Variables map to the same
        // independent assignment for repeated (type,period) identities.
        private static bool Eval(int[] leafIndexes, int[] ops, int count, int assignment)
        {
            bool value = (assignment & (1 << leafIndexes[0])) != 0;
            for (int i = 1; i < count; i++)
            {
                bool right = (assignment & (1 << leafIndexes[i])) != 0;
                value = ops[i - 1] == 0 ? (value && right) : (value || right);
            }
            return value;
        }

        public static NQCanonicalResultV3 Analyze(
            int count, int[] types, int[] periods, int[] ops,
            int reverse, int stopTicks, int targetTicks, int maxDailyEntries)
        {
            if (count < 1 || count > 4 || types == null || periods == null ||
                types.Length < count || periods.Length < count ||
                ops == null || ops.Length < count - 1 ||
                reverse < 0 || reverse > 1 || stopTicks < 1 ||
                targetTicks < 0 || maxDailyEntries < 1 || maxDailyEntries > 2)
                throw new ArgumentException("Invalid canonical generator configuration");

            string[] leaves = new string[count];
            int warmup = 0;
            for (int i = 0; i < count; i++)
            {
                if (types[i] < 0 || types[i] > 9 || periods[i] < 2 ||
                    periods[i] > 117)
                    throw new ArgumentException("Invalid active indicator gene");
                leaves[i] = LeafKey(types[i], periods[i]);
                warmup = Math.Max(warmup,
                    types[i] == 9 ? (2 * periods[i] + 4) : periods[i] + 4);
                if (i > 0 && ops[i-1] != 0 && ops[i-1] != 1)
                    throw new ArgumentException("Unknown boolean combination gene");
            }

            string[] unique = leaves.Distinct()
                .OrderBy(x => x, StringComparer.Ordinal).ToArray();
            int[] indexes = leaves.Select(x => Array.IndexOf(unique, x)).ToArray();
            int states = 1 << unique.Length; // at most 16
            bool[] full = new bool[states];
            for (int m = 0; m < states; m++)
                full[m] = Eval(indexes, ops, count, m);

            // A variable is essential iff flipping it can change the output.
            List<int> essential = new List<int>();
            for (int j = 0; j < unique.Length; j++)
            {
                bool used = false;
                for (int m = 0; m < states; m++)
                {
                    if (full[m] != full[m ^ (1 << j)])
                    {
                        used = true;
                        break;
                    }
                }
                if (used)
                    essential.Add(j);
            }

            // Recompute the truth table over only essential variables.
            // Nonessential bits are held at 0, which is logically equivalent.
            StringBuilder truth = new StringBuilder();
            for (int m = 0; m < (1 << essential.Count); m++)
            {
                int original = 0;
                for (int j = 0; j < essential.Count; j++)
                    if ((m & (1 << j)) != 0)
                        original |= 1 << essential[j];
                truth.Append(full[original] ? '1' : '0');
            }

            string key = "BCANv1:" +
                String.Join(",", essential.Select(j => unique[j]).ToArray()) +
                ";tt=" + truth.ToString();

            // Warmup is included deliberately: two boolean-equivalent rules
            // may trade on DIFFERENT bars when a redundant slow leaf delays
            // the V2 intra-session signal readiness.
            string runtime = key + ";warmup=" + warmup +
                ";reverse=" + reverse + ";SL=" + stopTicks +
                ";TP=" + targetTicks + ";daily=" + maxDailyEntries;

            // Stable short evidence ID (not for authentication/cryptography).
            byte[] bytes = Encoding.UTF8.GetBytes(runtime);
            string hash;
            using (var sha = SHA256.Create())
            {
                byte[] digest = sha.ComputeHash(bytes);
                hash = BitConverter.ToString(digest, 0, 12).Replace("-", "");
            }

            return new NQCanonicalResultV3
            {
                BooleanKey = key, RuntimeKey = runtime,
                Fingerprint = "NQBC3_" + hash,
                ActiveLeaves = count, EffectiveLeaves = essential.Count,
                WarmupBars = warmup
            };
        }
    }
}
