// S0.85 V24: 36-month representative LONG-HORIZON M1,
 // every synthetic weekday in 2020–22, with full 210 bars/session.
 // Actually executes conservative V12 fills and V9 economic score for
 // every unique generated genome. Never uses an artificial fitness
 // callback, never uses 2023+ data or makes a market profitability claim.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class NQV24LongHorizonTest
{
    static void A(bool ok,string msg)
    {if(!ok)throw new Exception("NQ_V24_LONG_FAIL "+msg);}
    static int[] Genes(int a,int b)
    {
        return new[]{
            2,a*11+1,12,b*11+2,12,999,12,1319,12,
            0,0,0,0,20,32,2,0,14,15,25
        };
    }
    static NQEvolutionConfigV12 GA(int generations)
    {
        return new NQEvolutionConfigV12{
            Population=24,Generations=generations,Elites=3,
            Tournament=3,Seed=20261106,MaxAttempts=6000,
            ImmigrantPercent=25,MutationPercent=18,
            ResetAfterStagnantGenerations=3
        };
    }
    static void Same(
        NQHistoricalResultV12 baseline,
        NQHistoricalResultV12 improved,string label)
    {
        A(baseline.Valid&&improved.Valid&&
          baseline.Score==improved.Score&&
          baseline.Net==improved.Net&&
          baseline.SignalCount==improved.SignalCount&&
          baseline.DailyBlocked==improved.DailyBlocked&&
          baseline.AtrBlocked==improved.AtrBlocked&&
          baseline.RiskBlocked==improved.RiskBlocked&&
          baseline.StopFills==improved.StopFills&&
          baseline.TargetFills==improved.TargetFills&&
          baseline.TimeFills==improved.TimeFills&&
          baseline.AmbiguousStops==improved.AmbiguousStops&&
          baseline.Trades.Count==improved.Trades.Count&&
          baseline.Executed.Count==improved.Executed.Count,
          "bitwise V12 economy/control parity "+label);
        for(int i=0;i<baseline.Trades.Count;i++)
        {
            var x=baseline.Trades[i];var y=improved.Trades[i];
            var a=baseline.Executed[i];var b=improved.Executed[i];
            A(x.NetProfitUSD==y.NetProfitUSD&&
              x.MaeCurrency==y.MaeCurrency&&
              x.MfeCurrency==y.MfeCurrency&&
              a.EntryTime==b.EntryTime&&a.ExitTime==b.ExitTime&&
              a.Side==b.Side&&a.Quantity==b.Quantity&&
              a.EntryPrice==b.EntryPrice&&
              a.ExitPrice==b.ExitPrice&&
              a.RoundTripFeesUSD==b.RoundTripFeesUSD,
              "identical trade/time/fees/MAE/MFE "+label+" #"+i);
        }
    }
    public static int Main()
    {
        string root=Path.Combine(Path.GetTempPath(),
            "NQ_V24_LONG_"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var data=NQNativeSynthetic36V24.Build();
            A(data.Manifest.FullSessionsByMonth.Length==36&&
              data.Manifest.FullSessionsByMonth.All(x=>x>=20)&&
              data.Manifest.CompleteRthDays>=780 &&
              data.Bars.Count>160000,
              "36 full months ~3 calendar years 210 M1 bars/weekday");
            var cache=new NQNativeSignalCacheV14(
                data.Bars,64L*1024*1024,64L*1024*1024,
                NQNativeConditionCatalogV19.Count,
                NQNativeExpandedResearchV19.Direction);
            A(cache.CompressionActive&&
              cache.HasSufficientMonthCoverage&&
              cache.WorkingBars==data.Manifest.CompleteRthDays*120,
              "realistic full-session 36-month compressed 120 M1 source");
            var memo=new NQNativeFeatureMemoV21(
                cache,256L*1024*1024);
            var prepared=new NQNativePreparedEconomicV24(cache,memo);
            int pairs=0,trades=0;
            foreach(var x in new[]{
                 Genes(36,55),Genes(58,72),
                 Genes(81,95),Genes(101,115),
                 Genes(44,118)
            })
            {
                var standard=memo.Evaluate(x);
                var fast=prepared.Evaluate(x);
                Same(standard,fast,"families="+x[1]+","+x[3]);
                pairs++;trades+=standard.Trades.Count;
            }
            A(prepared.PreparedNumericLeaves==2*pairs &&
              trades>=0&&memo.UsedBytes<=memo.MaxBytes,
              "all 10 numeric leaves prepared and memory-budgeted");

            string ledger=Path.Combine(root,"economic_36mo.tsv"),
                ranking=Path.Combine(root,"ranked_36mo.tsv");
            var result=NQNativeEconomicScaleV24.Run(
                data,Genes(36,115),GA(2),ledger,ranking,5,
                64L*1024*1024,256L*1024*1024);
            int expected=24+(2-1)*(24-3);
            A(expected==45&&result.SourceBars>160000&&
              result.WorkingBars>90000&&
              result.UniqueGenomes==expected&&
              result.NewEconomicBacktests==expected&&
              result.ReusedGenomes==0 &&
              result.MissingOrInvalidFitness==0&&
              result.PreparedGenomes==expected&&
              result.PreparedNumericLeaves>0&&
              result.NumericTablesCreated>0&&
              result.ElapsedMilliseconds>0,
              "45 real V12 economic M1 backtests, >90k RTH bars each");
            A(result.FeaturePayloadBytes<=256L*1024*1024&&
              result.SignalPayloadBytes<=64L*1024*1024&&
              result.AtrPayloadBytes<=67108864 &&
              result.ProcessPeakWorkingSetBytes>0&&
              result.MaxObservedManagedBytes>0&&
              result.FullBacktestsPerSecond>0&&
              result.MillionBarVisitsPerSecond>0,
              "honest throughput and cache-payload diagnostics");
            A(File.ReadLines(ledger).Count()==expected+1&&
              File.ReadLines(ranking).Count()==6,
              "persisted net/PF/DD for ALL 45 unique full M1 simulations");

            var replay=NQNativeEconomicScaleV24.Run(
                data,Genes(36,115),GA(2),ledger,ranking,5,
                64L*1024*1024,256L*1024*1024);
            A(replay.NewEconomicBacktests==0&&
              replay.ReusedGenomes==expected &&
              replay.UniqueGenomes==expected&&
              result.Top.Zip(replay.Top,(a,b)=>
                a.Canonical==b.Canonical &&
                a.Net==b.Net&&
                a.ProfitFactor==b.ProfitFactor&&
                a.ClosedDrawdown==b.ClosedDrawdown&&
                a.Score==b.Score).All(x=>x),
              "restart repeats ZERO economic M1 backtests");

            var extended=NQNativeEconomicScaleV24.Run(
                data,Genes(36,115),GA(3),ledger,ranking,5,
                64L*1024*1024,256L*1024*1024);
            A(extended.NewEconomicBacktests==21&&
              extended.ReusedGenomes==45&&
              extended.UniqueGenomes==66,
              "one more generation adds 21 real full-length V12 fills"+
              " without recomputing the 45 saved");
            var secondReplay=NQNativeEconomicScaleV24.Run(
                data,Genes(36,115),GA(3),ledger,ranking,5,
                64L*1024*1024,256L*1024*1024);
            A(secondReplay.NewEconomicBacktests==0&&
              secondReplay.ReusedGenomes==66,
              "extended economic journal resumes 66 with 0 new M1 tests");

            // Same manifest metadata SHA, different effective OHLCV must
            // never reuse a stale V24 ledger.
            var changed=NQNativeSynthetic36V24.Build(20261106,true);
            A(changed.Manifest.Sha256==data.Manifest.Sha256&&
              NQNativeReproducibilityV23.SourceBarsHash(changed)!=
              NQNativeReproducibilityV23.SourceBarsHash(data),
              "raw-header hash collision does not hide bar changes");
            try
            {
                NQNativeEconomicScaleV24.Run(
                    changed,Genes(36,115),GA(2),ledger,ranking,5,
                    64L*1024*1024,256L*1024*1024);
                throw new Exception("ACCEPTED_DIFFERENT_LONG_HISTORY");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("MISMATCH"),
                "V24 source/content SHA protects the ledger");}

            Console.WriteLine("NQ_V24_LONG_HORIZON_ECON_PASS"+
                " syntheticFullMonths=36"+
                " sessions="+data.Manifest.CompleteRthDays+
                " sourceBars="+data.Bars.Count+
                " workingBars="+cache.WorkingBars+
                " exactV12ParityGenomes="+pairs+
                " exactV12ParityTrades="+trades+
                " firstNewBacktests="+result.NewEconomicBacktests+
                " extensionNewBacktests="+extended.NewEconomicBacktests+
                " totalFullEconomicBacktests="+extended.UniqueGenomes+
                " restartNewBacktests="+replay.NewEconomicBacktests+
                " firstMs="+result.ElapsedMilliseconds+
                " fullBacktestsPerSecond="+
                    result.FullBacktestsPerSecond.ToString("F4",
                        System.Globalization.CultureInfo.InvariantCulture)+
                " barsPerSecMillions="+
                    result.MillionBarVisitsPerSecond.ToString("F4",
                        System.Globalization.CultureInfo.InvariantCulture)+
                " maxWorkingSetMiB="+
                    (result.ProcessPeakWorkingSetBytes/1048576.0)
                        .ToString("F2",
                         System.Globalization.CultureInfo.InvariantCulture)+
                " shaProtected=TRUE");
            Console.WriteLine("SYNTHETIC_36_MONTHS_WITH_FULL_V12_FILLS_"+
                "NOT_REAL_NQ_100K_NOT_PROVEN_NO_NATIVE_NT8");
            return 0;
        }
        finally{Directory.Delete(root,true);}
    }
}
