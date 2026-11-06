// S0.85 V24 — long-horizon FULL conservative V12 M1 economics
// scale runner. Not a synthetic-fitness oracle. Records actual
// bar-by-bar fills and V9 economic score per unique 20-gene EXCANv19
// genome in the persistent V21 ledger. Precompiles leaf feature
// tables per genome. A second run replays journal scores with zero
// new economic backtests. Supports 10k/100k GA settings but never
// asserts those workloads are fast or profitable without measurement.
// The only allowed source is 2020–22 development; never opens OOS.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQEconomicScaleResultV24
    {
        public int UniqueGenomes,NewEconomicBacktests,ReusedGenomes;
        public int SourceBars,WorkingBars,CompleteSessions;
        public int NumericTablesCreated,NumericTableReuses,TableEvictions;
        public int PreparedGenomes,PreparedNumericLeaves;
        public int MissingOrInvalidFitness;
        public long ElapsedMilliseconds,MaxObservedManagedBytes;
        public long ProcessPeakWorkingSetBytes,FeaturePayloadBytes;
        public long SignalPayloadBytes,AtrPayloadBytes;
        public double FullBacktestsPerSecond,MillionBarVisitsPerSecond;
        public string SourceSeriesSHA256,ConfigSHA256,LedgerPath;
        public NQEvolutionSummaryV12 Evolution;
        public readonly List<NQEconomicRowV21> Top=
            new List<NQEconomicRowV21>();
    }

    public static class NQNativeEconomicScaleV24
    {
        public const string EngineVersion=
            "S0.85_V24_PREPARED_VALUES_EXCANv19_V12_FILLED_M1_V9";
        public static NQEconomicScaleResultV24 Run(
            NQDataLoadV16 development,int[] baseline,
            NQEvolutionConfigV12 genetic,string ledgerPath,
            string rankingPath,int topCount,
            long signalBudgetBytes,long featureBudgetBytes,
            bool preparedSignals=true,int minimumFullSessionsPerMonth=15)
        {
            if(development==null||development.Manifest==null||
               development.Bars==null||
               development.Manifest.Partition!=
                    NQDataPartitionV16.Development2020_2022||
               development.Manifest.FullSessionsByMonth==null||
               development.Manifest.FullSessionsByMonth.Length!=36||
               development.Manifest.FullSessionsByMonth.Any(x=>
                    x<minimumFullSessionsPerMonth)||
               baseline==null||baseline.Length!=20||genetic==null||
               String.IsNullOrWhiteSpace(ledgerPath)||
               String.IsNullOrWhiteSpace(rankingPath)||
               ledgerPath==rankingPath||topCount<1||topCount>1000||
               signalBudgetBytes<1024*1024||
               featureBudgetBytes<1024*1024||
               minimumFullSessionsPerMonth<1||
               minimumFullSessionsPerMonth>23)
                throw new ArgumentException(
                    "V24_REQUIRES_36_COMPLETE_DEV_MONTHS_AND_BUDGETS");
            genetic.Validate();
            if(NQNativeExitCanonicalV19.Analyze(baseline).IsRedundant)
                throw new ArgumentException("V24_REDUNDANT_20_GENE_BASELINE");
            string rawSHA=NQNativeReproducibilityV23.SourceBarsHash(
                development);
            var chrono=Stopwatch.StartNew();
            var source=new NQNativeSignalCacheV14(
                development.Bars,signalBudgetBytes,67108864,
                NQNativeConditionCatalogV19.Count,
                NQNativeExpandedResearchV19.Direction);
            if(!source.CompressionActive||
               !source.HasSufficientMonthCoverage)
                throw new InvalidOperationException(
                    "V24_REQUIRES_COMPLETE_RTH_AND_15_SESSIONS_PER_MONTH");
            var memo=new NQNativeFeatureMemoV21(source,
                featureBudgetBytes);
            var compiled=new NQNativePreparedEconomicV24(source,memo);
            Func<int[],NQHistoricalResultV12> scorer=
                preparedSignals?compiled.Evaluate:memo.Evaluate;
            string economicFingerprint=NQNativeReproducibilityV23.SHA(
                EngineVersion+"\n"+
                NQNativeEconomicLedgerV21.Fingerprint(
                    genetic,baseline,true)+"\n"+
                "conservativeM1V12=UNCHANGED\n"+
                "scorerIsPreparedSemanticallyEquivalent="+
                    preparedSignals.ToString());
            // Prepared and ordinary baseline results MUST use distinct
            // score ledgers unless a differential parity test has been
            // run; no mixing of unknown versions or costs.
            var result=new NQEconomicScaleResultV24{
                SourceSeriesSHA256=rawSHA,
                ConfigSHA256=economicFingerprint,
                LedgerPath=ledgerPath,
                SourceBars=source.SourceBars,
                WorkingBars=source.WorkingBars,
                CompleteSessions=development.Manifest.CompleteRthDays
            };
            using(var ledger=new NQNativeEconomicLedgerV21(
                ledgerPath,rawSHA,economicFingerprint))
            {
                Exception fatal=null;
                var engine=new NQEvolutionEngineV12(
                    NQNativeExitCanonicalV19.DefaultDomains(
                        baseline,true),genetic,
                    NQNativeExitCanonicalV19.Analyze);
                result.Evolution=engine.Run(genome=>
                {
                    if(fatal!=null)return -1.0e12;
                    try{return ledger.Score(genome,scorer);}
                    catch(Exception ex)
                    {
                        fatal=ex;
                        return -1.0e12;
                    }
                });
                if(fatal!=null)
                    throw new InvalidOperationException(
                        "V24_FATAL_ECONOMIC_OR_JOURNAL_FAILURE",fatal);
                ledger.Flush();
                result.UniqueGenomes=result.Evolution.Evaluated.Count;
                result.NewEconomicBacktests=ledger.Fresh;
                result.ReusedGenomes=ledger.Reused;
                result.MissingOrInvalidFitness=
                    result.Evolution.InvalidFitness;
                result.Top.AddRange(ledger.Ranked.Take(topCount));
                ledger.WriteRanking(rankingPath,topCount);
            }
            chrono.Stop();
            result.ElapsedMilliseconds=chrono.ElapsedMilliseconds;
            result.FullBacktestsPerSecond=chrono.Elapsed.TotalSeconds>0?
                result.NewEconomicBacktests/chrono.Elapsed.TotalSeconds:0;
            result.MillionBarVisitsPerSecond=
                chrono.Elapsed.TotalSeconds>0?
                ((double)result.NewEconomicBacktests*
                    result.WorkingBars/1000000.0)/
                    chrono.Elapsed.TotalSeconds:0;
            result.NumericTablesCreated=memo.FeatureBuilds;
            result.NumericTableReuses=memo.FeatureHits;
            result.TableEvictions=memo.Evictions;
            result.FeaturePayloadBytes=memo.UsedBytes;
            result.SignalPayloadBytes=source.UsedSignalBytes;
            result.AtrPayloadBytes=source.UsedAtrBytes;
            result.PreparedGenomes=compiled.PreparedGenomes;
            result.PreparedNumericLeaves=compiled.PreparedNumericLeaves;
            result.MaxObservedManagedBytes=GC.GetTotalMemory(false);
            using(var process=Process.GetCurrentProcess())
                result.ProcessPeakWorkingSetBytes=
                    process.PeakWorkingSet64;
            return result;
        }
    }
}
