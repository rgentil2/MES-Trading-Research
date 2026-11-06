// S0.82 V21 headless bulk economic research engine, 1320-condition
// 20-gene V19 GA with ACTUAL V12 M1 conservative economic callbacks.
// Optional numerical family memo to reuse one formula evaluation for
// 11 predicates, durable source/scorer-bound economic journal, final
// rankings and exact trade/fill audit for a bounded top-N shortlist.
// Does not use 2023+ data, NT8 native fills or place orders.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQBulkEconomicResultV21
    {
        public int Unique,NewEconomicBacktests,ReusedEconomicBacktests;
        public int FinalistBacktests,InvalidFitness,FeatureBuilds;
        public int FeatureHits,FeatureEvictions,OriginalSignalMisses;
        public long FeatureMemoryBytes;
        public long ElapsedMilliseconds;
        public string SourceSHA256,CampaignSHA256,RankingPath,TradePath;
        public NQEvolutionSummaryV12 Evolution;
        public readonly List<NQEconomicRowV21> Top=
            new List<NQEconomicRowV21>();
    }
    public static class NQNativeBulkEconomicV21
    {
        static string Num(double x)
        {return x.ToString("R",CultureInfo.InvariantCulture);}
        static string B64(string x)
        {return Convert.ToBase64String(Encoding.UTF8.GetBytes(x));}

        public static NQBulkEconomicResultV21 Run(
            IList<NQTimedBarV12> development,
            int[] baseline,NQEvolutionConfigV12 evolution,
            string developmentSha256,string ledgerPath,
            string rankingPath,string finalistTradesPath,
            int topCount,long maxSignalCacheBytes,
            long maxFeatureCacheBytes,bool useFeatureMemo=true)
        {
            if(development==null||baseline==null||baseline.Length!=20||
               evolution==null||String.IsNullOrWhiteSpace(ledgerPath)||
               String.IsNullOrWhiteSpace(rankingPath)||
               String.IsNullOrWhiteSpace(finalistTradesPath)||
               topCount<1||topCount>1000 ||
               maxSignalCacheBytes<1||maxFeatureCacheBytes<1)
                throw new ArgumentException("V21 development, GA, caps and durable output paths required");
            evolution.Validate();
            var initial=NQNativeExitCanonicalV19.Analyze(baseline);
            if(initial.IsRedundant)
                throw new ArgumentException("Redundant V19 initial genome");
            if(ledgerPath==rankingPath||ledgerPath==finalistTradesPath||
               rankingPath==finalistTradesPath)
                throw new ArgumentException("Ledger/ranking/trades need distinct paths");
            var stopwatch=Stopwatch.StartNew();
            var cache=new NQNativeSignalCacheV14(development,
                maxSignalCacheBytes,67108864,
                NQNativeConditionCatalogV19.Count,
                NQNativeExpandedResearchV19.Direction);
            NQNativeFeatureMemoV21 memo=useFeatureMemo?
                new NQNativeFeatureMemoV21(cache,maxFeatureCacheBytes):null;
            Func<int[],NQHistoricalResultV12> scorer=memo==null?
                (Func<int[],NQHistoricalResultV12>)(
                    g=>cache.EvaluateExpanded(
                        g,NQNativeExitCanonicalV19.Analyze)):
                g=>memo.Evaluate(g);
            var ranges=NQNativeExitCanonicalV19.DefaultDomains(
                baseline,true);
            string signature=NQNativeEconomicLedgerV21.Fingerprint(
                evolution,baseline,true);
            var result=new NQBulkEconomicResultV21{
                SourceSHA256=developmentSha256,
                CampaignSHA256=signature,
                RankingPath=rankingPath,
                TradePath=finalistTradesPath
            };
            using(var ledger=new NQNativeEconomicLedgerV21(
                ledgerPath,developmentSha256,signature))
            {
                // V12 GA catches fitness exceptions as invalid fitness.
                // Preserve fatal I/O/evaluator problems and THROW after
                // the run instead of silently reporting fake winners.
                Exception fatal=null;
                var engine=new NQEvolutionEngineV12(
                    ranges,evolution,NQNativeExitCanonicalV19.Analyze);
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
                        "V21_FATAL_ECONOMIC_LEDGER_OR_SIMULATION",fatal);
                ledger.Flush();
                result.Unique=result.Evolution.Evaluated.Count;
                result.NewEconomicBacktests=ledger.Fresh;
                result.ReusedEconomicBacktests=ledger.Reused;
                result.InvalidFitness=result.Evolution.InvalidFitness;
                result.Top.AddRange(ledger.Ranked.Take(topCount));
                ledger.WriteRanking(rankingPath,topCount);
                using(var writer=new StreamWriter(finalistTradesPath,
                    false,new UTF8Encoding(false)))
                {
                    writer.WriteLine("canonicalBase64\tgeneVectorBase64"+
                        "\tentryTimeET\texitTimeET\tside\tquantity"+
                        "\tentryPrice\texitPrice\tfeeUSD\t"+
                        "netUSD\tMAEUSD\tMFEUSD");
                    foreach(var row in result.Top)
                    {
                        // Rank-only shortlist is re-evaluated to obtain
                        // complete fill receipts. Top count is capped.
                        // Never serialize all 100k fill objects in RAM.
                        var historical=scorer(row.Genes);
                        if(!historical.Valid ||
                           historical.Trades.Count!=historical.Executed.Count||
                           Math.Abs(historical.Score-row.Score)>1e-7 ||
                           Math.Abs(historical.Net-row.Net)>0.03 ||
                           historical.Trades.Count!=row.Trades)
                            throw new InvalidOperationException(
                                "V21_FINALIST_M1_LEDGER_MISMATCH");
                        result.FinalistBacktests++;
                        string id=B64(row.Canonical);
                        string genes=B64(String.Join("/",
                            row.Genes.Select(x=>x.ToString(
                                CultureInfo.InvariantCulture))));
                        for(int j=0;j<historical.Executed.Count;j++)
                        {
                            var e=historical.Executed[j];
                            var t=historical.Trades[j];
                            if(e.EntryTime!=t.EntryTime||
                               e.ExitTime!=t.ExitTime)
                                throw new InvalidOperationException(
                                    "V21_FINALIST_FILL_TRADE_MISMATCH");
                            writer.WriteLine(String.Join("\t",new[]{
                                id,genes,
                                e.EntryTime.ToString(
                                    "yyyy-MM-ddTHH:mm:ss",
                                    CultureInfo.InvariantCulture),
                                e.ExitTime.ToString(
                                    "yyyy-MM-ddTHH:mm:ss",
                                    CultureInfo.InvariantCulture),
                                e.Side.ToString(CultureInfo.InvariantCulture),
                                e.Quantity.ToString(CultureInfo.InvariantCulture),
                                Num(e.EntryPrice),Num(e.ExitPrice),
                                Num(e.RoundTripFeesUSD),
                                Num(t.NetProfitUSD),Num(t.MaeCurrency),
                                Num(t.MfeCurrency)
                            }));
                        }
                    }
                }
            }
            stopwatch.Stop();
            result.ElapsedMilliseconds=stopwatch.ElapsedMilliseconds;
            if(memo!=null)
            {
                result.FeatureBuilds=memo.FeatureBuilds;
                result.FeatureHits=memo.FeatureHits;
                result.FeatureEvictions=memo.Evictions;
                result.FeatureMemoryBytes=memo.UsedBytes;
            }
            result.OriginalSignalMisses=cache.CacheMisses;
            return result;
        }
    }
}
