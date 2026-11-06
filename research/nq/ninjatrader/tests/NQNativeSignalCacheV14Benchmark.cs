// V14 controlled large-window performance profile, NOT a real NQ backtest.
// 45 synthetic calendar days of full 24-hour M1 data (~64,800 bars).
// Compare original V12 scans versus V14 compressed 09:30-11:29 path.
// Timings on CI are platform-dependent and are NOT used as hard gates.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using NinjaTrader.NinjaScript.Strategies;
internal static class V14Benchmark
{
    private static void T(bool x,string message)
    {if(!x)throw new Exception("NQ_V14_PERF_FAIL "+message);}
    private static List<NQTimedBarV12> Fixture(int days)
    {
        var rows=new List<NQTimedBarV12>(days*1440);
        var random=new Random(20261106);
        double price=15000;
        var first=new DateTime(2021,7,1,0,0,0);
        for(int d=0;d<days;d++)
        {
            DateTime start=first.AddDays(d);
            for(int m=0;m<1440;m++)
            {
                double o=price;
                price+=(random.NextDouble()-0.5)*3+
                    (m>=570&&m<=687?0.2:0);
                rows.Add(new NQTimedBarV12(start.AddMinutes(m),
                    new NQBarV11(o,Math.Max(o,price)+0.7,
                    Math.Min(o,price)-0.7,price,100+random.Next(500))));
            }
        }
        return rows;
    }
    public static int Main()
    {
        var source=Fixture(45);
        var cache=new NQNativeSignalCacheV14(source,64L*1024*1024);
        T(cache.CompressionActive,"complete sessions compress");
        T(cache.SourceBars==64800,"45 complete 24h days");
        T(cache.WorkingBars==5400,"45 research sessions x 120 M1");
        T(cache.WorkingBars*10<cache.SourceBars,
            "scan reduction exceeds 10x at 24-hour M1 ingestion");

        var gen=new NQUniqueSearchV11(
            NQUniqueSearchV11.Smoke(),20261106);
        var genomes=new List<int[]>();
        while(genomes.Count<160 && gen.Attempted<5000)
        {
            var g=gen.TryNext();
            if(g!=null)genomes.Add(g.Genes);
        }
        T(genomes.Count==160,"enough unique strategies");
        var t=Stopwatch.StartNew();
        var reference=new List<NQHistoricalResultV12>();
        foreach(var genes in genomes)
            reference.Add(NQNativeHistoricalEvaluatorV12.Evaluate(source,genes));
        t.Stop();
        long originalMs=t.ElapsedMilliseconds;

        t.Restart();
        var cached=new List<NQHistoricalResultV12>();
        foreach(var genes in genomes)
            cached.Add(cache.Evaluate(genes));
        t.Stop();
        long coldMs=t.ElapsedMilliseconds;

        t.Restart();
        for(int i=0;i<genomes.Count;i++)
        {
            var score=cache.Evaluate(genomes[i]);
            T(score.Score==reference[i].Score&&
              score.Trades.Count==reference[i].Trades.Count,
              "cached evaluation must not change GA objective or trade count");
        }
        t.Stop();
        long warmMs=t.ElapsedMilliseconds;
        T(cache.UsedSignalBytes<=cache.MaxSignalBytes&&
          cache.UsedAtrBytes<=cache.MaxAtrBytes,
          "both caches respect declared memory budgets");
        Console.WriteLine("NQ_V14_BENCHMARK_PASS sourceBars="+
            source.Count+" workingBars="+cache.WorkingBars+
            " genomeCount="+genomes.Count+
            " originalMs="+originalMs+
            " coldMs="+coldMs+
            " warmMs="+warmMs+
            " cachedSignalTables="+cache.Entries+
            " signalMiB="+(cache.UsedSignalBytes/(1024.0*1024)).ToString("F3")+
            " atrMiB="+(cache.UsedAtrBytes/(1024.0*1024)).ToString("F3"));
        Console.WriteLine("BENCHMARK_SYNTHETIC_M1_ONLY_NOT_REAL_2020_22_NQ");
        return 0;
    }
}
