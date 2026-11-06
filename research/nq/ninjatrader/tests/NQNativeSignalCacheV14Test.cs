// S0.74 — differential parity of V14 cached RTH signals and EXACT
// V12 conservative M1 simulator, driven by identical immutable bars.
// This verifies software equivalence, not NinjaTrader 8 fill parity.
// No actual NQ market history available in repository.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V14CacheTest
{
    private static void Check(bool b,string reason)
    {if(!b)throw new Exception("NQ_V14_CACHE_FAIL "+reason);}
    private static List<NQTimedBarV12> Source()
    {
        var b=new List<NQTimedBarV12>();
        var rng=new Random(20261106);
        var initial=new DateTime(2021,6,1);
        double px=15000;
        for(int day=0;day<12;day++)
        {
            // 12 consecutive daily sessions, including weekends, are
            // deliberately synthetic. Only time-order invariants tested.
            var start=initial.AddDays(day).AddHours(9).AddMinutes(30);
            for(int m=0;m<120;m++)
            {
                double op=px;
                px+=0.6+Math.Sin(m/9.0)*2.4+
                    (rng.NextDouble()-0.5)*8;
                double hi=Math.Max(op,px)+1.5+rng.NextDouble();
                double lo=Math.Min(op,px)-1.5-rng.NextDouble();
                b.Add(new NQTimedBarV12(start.AddMinutes(m),
                    new NQBarV11(op,hi,lo,px,200+rng.Next(900))));
            }
        }
        return b;
    }
    private static List<NQTimedBarV12> WithExtraHours()
    {
        var raw=Source();
        var widened=new List<NQTimedBarV12>();
        for(int day=0;day<12;day++)
        {
            var daily=raw.GetRange(day*120,120);
            DateTime early=daily[0].Time.Date.AddHours(8);
            double reference=daily[0].Bar.Open;
            for(int i=0;i<90;i++)
            {
                double px=reference+Math.Sin(i/13.0)*5;
                widened.Add(new NQTimedBarV12(early.AddMinutes(i),
                    new NQBarV11(px,px+2,px-2,px,300)));
            }
            widened.AddRange(daily);
            DateTime late=daily[119].Time.AddMinutes(1);
            for(int i=0;i<60;i++)
            {
                double px=daily[119].Bar.Close+Math.Sin(i/11.0)*3;
                widened.Add(new NQTimedBarV12(late.AddMinutes(i),
                    new NQBarV11(px,px+2,px-2,px,150)));
            }
        }
        return widened;
    }
    private static void Equal(NQHistoricalResultV12 slow,
                              NQHistoricalResultV12 fast,string label)
    {
        Check(slow.Valid==fast.Valid&&slow.Reason==fast.Reason,
              label+" validity/reason");
        Check(slow.Score==fast.Score&&Math.Abs(slow.Net-fast.Net)<1e-9,
              label+" score/net");
        Check(slow.Trades.Count==fast.Trades.Count,label+" trade count");
        Check(slow.SignalCount==fast.SignalCount &&
              slow.RiskBlocked==fast.RiskBlocked &&
              slow.AtrBlocked==fast.AtrBlocked &&
              slow.DailyBlocked==fast.DailyBlocked &&
              slow.StopFills==fast.StopFills &&
              slow.TargetFills==fast.TargetFills &&
              slow.TimeFills==fast.TimeFills &&
              slow.AmbiguousStops==fast.AmbiguousStops,
              label+" all decision and fill counters");
        for(int i=0;i<slow.Trades.Count;i++)
        {
            var a=slow.Trades[i];var b=fast.Trades[i];
            Check(a.EntryTime==b.EntryTime&&a.ExitTime==b.ExitTime &&
                  Math.Abs(a.NetProfitUSD-b.NetProfitUSD)<1e-9 &&
                  Math.Abs(a.MaeCurrency-b.MaeCurrency)<1e-9 &&
                  Math.Abs(a.MfeCurrency-b.MfeCurrency)<1e-9,
                  label+" trade-by-trade historical parity");
        }
    }
    public static int Main()
    {
        var src=WithExtraHours();
        var cache=new NQNativeSignalCacheV14(src,16*1024*1024);
        Check(cache.SourceBars==src.Count&&cache.RthBars==12*118,
            "RTH-only cached bars excluding 11:28 and 11:29");
        Check(cache.CompressionActive&&cache.WorkingBars==12*120 &&
            cache.WorkingBars<cache.SourceBars/2,
            "complete sessions reduce overnight scanning by more than 50%");
        Check(cache.CacheMisses==0&&cache.UsedSignalBytes==0,
            "lazy cache at construction");

        // Test all 132 condition types at 6, 12 and 24-bar periods,
        // independently comparing exact historical prefixes, including
        // warmup and daily session reset. No next-bar lookahead.
        int comparisons=0;
        for(int type=0;type<132;type++)
        {
            foreach(int period in new[]{6,12,24})
            {
                var prefix=new List<NQBarV11>();
                DateTime day=DateTime.MinValue;
                for(int i=0;i<src.Count;i++)
                {
                    int clock=src[i].Time.Hour*100+
                        src[i].Time.Minute;
                    if(src[i].Time.Date!=day)
                    {prefix.Clear();day=src[i].Time.Date;}
                    if(clock<930||clock>1127)
                    {
                        Check(cache.GetSignal(i,type,period)==0,
                            "non-RTH must be neutral");
                        continue;
                    }
                    prefix.Add(src[i].Bar);
                    bool bull,bear;
                    bool ready=NQNativeConditionsV11.TryEvaluate(
                        prefix,type,period,out bull,out bear);
                    int expected=!ready?0:bull?1:bear?-1:0;
                    Check(cache.GetSignal(i,type,period)==expected,
                        "type="+type+" p="+period+" i="+i+
                        " cache/prefix mismatch");
                    comparisons++;
                }
            }
        }
        Check(cache.CacheMisses==396,
            "132 types x 3 periods exactly once cached");
        Check(cache.CacheHits>comparisons-500,
            "repeated probes reuse cache");

        // Conservatively compare complete trades and original V9
        // economic score for many unique genome/exit combinations.
        var generator=new NQUniqueSearchV11(NQUniqueSearchV11.Smoke(),20261106);
        var genomes=new List<int[]>();
        while(genomes.Count<120&&generator.Attempted<3000)
        {
            var x=generator.TryNext();
            if(x!=null)genomes.Add(x.Genes);
        }
        Check(genomes.Count==120,"120 unique V11 genome samples");
        var timer=Stopwatch.StartNew();
        var slow=new List<NQHistoricalResultV12>();
        foreach(var genes in genomes)
            slow.Add(NQNativeHistoricalEvaluatorV12.Evaluate(src,genes));
        timer.Stop();long uncachedMs=timer.ElapsedMilliseconds;
        timer.Restart();
        for(int k=0;k<genomes.Count;k++)
        {
            var fast=cache.Evaluate(genomes[k]);
            Equal(slow[k],fast,"candidate="+k);
        }
        timer.Stop();long cachedMs=timer.ElapsedMilliseconds;
        Check(cache.UsedSignalBytes<=cache.MaxSignalBytes,
            "cache never exceeds signal-array memory cap");
        Check(cache.UsedAtrBytes<=cache.MaxAtrBytes,
            "ATR caches are also bounded");

        // Strong no-lookahead property: modifying the later source list
        // cannot change earlier cached or evaluated results, because the
        // V14 source copy was frozen when constructed.
        int checkIndex=200;
        int original=cache.GetSignal(checkIndex,3,12);
        var prior=cache.Evaluate(genomes[0]);
        var old=src[src.Count-1];
        src[src.Count-1]=new NQTimedBarV12(old.Time,
            new NQBarV11(1,2,0,1,5));
        Check(cache.GetSignal(checkIndex,3,12)==original,
            "cache remains frozen after source list mutation");
        Equal(prior,cache.Evaluate(genomes[0]),"snapshot immutability");

        // A single missing 11:29 M1 bar forces full-source fallback.
        // Never omit a bar required for a late time exit.
        var incomplete=WithExtraHours();
        int removeAt=incomplete.FindIndex(x=>
            x.Time.Date==new DateTime(2021,6,4) &&
            x.Time.Hour==11 && x.Time.Minute==29);
        Check(removeAt>=0,"synthetic missing-bar fixture");
        incomplete.RemoveAt(removeAt);
        var fallback=new NQNativeSignalCacheV14(incomplete,16*1024*1024);
        Check(!fallback.CompressionActive &&
            fallback.WorkingBars==fallback.SourceBars,
            "incomplete research session must disable compaction");
        foreach(var genes in genomes.Take(12))
            Equal(NQNativeHistoricalEvaluatorV12.Evaluate(incomplete,genes),
                  fallback.Evaluate(genes),"fallback");

        // ATR memoization is based on unfiltered source (including
        // overnight input) with a strict, independently bounded LRU.
        var limitedAtr=new NQNativeSignalCacheV14(WithExtraHours(),
            4*1024*1024,8L*src.Count);
        var atrGenome=(int[])genomes[0].Clone();
        atrGenome[0]=1;atrGenome[1]=0;atrGenome[2]=6;
        atrGenome[16]=1;atrGenome[17]=7;
        limitedAtr.Evaluate(atrGenome);
        atrGenome[17]=14;
        limitedAtr.Evaluate(atrGenome);
        Check(limitedAtr.AtrCacheMisses>=2 &&
              limitedAtr.AtrCacheEvictions>=1 &&
              limitedAtr.UsedAtrBytes<=limitedAtr.MaxAtrBytes,
              "ATR full-source LRU respects single-table budget");

        // Tiny signal cache is intentionally bounded; LRU evicts keys.
        var tiny=new NQNativeSignalCacheV14(Source(),2L*12*118);
        tiny.GetSignal(90,0,6);
        tiny.GetSignal(90,1,6);
        tiny.GetSignal(90,0,6);
        tiny.GetSignal(90,2,6);
        Check(tiny.Entries==2&&tiny.CacheEvictions==1 &&
              tiny.CacheHits==1 && tiny.CacheMisses==3 &&
              tiny.UsedSignalBytes==tiny.MaxSignalBytes,
              "strict LRU limits signal arrays");
        tiny.GetSignal(90,1,6);
        Check(tiny.CacheEvictions==2&&tiny.CacheMisses==4,
              "evicted table must be recomputed");

        try
        {
            new NQNativeSignalCacheV14(Source(),100);
            throw new Exception("missing min-cache budget guard");
        }
        catch(ArgumentException ex)
        {
            Check(ex.Message.Contains("too small"),
                "one-table minimum allocation budget");
        }
        try
        {
            new NQNativeCachedPipelineV14(Source(),
                genomes[0],new NQEvolutionConfigV12(),true,true,2000000);
            throw new Exception("missing required 36-month guard");
        }
        catch(InvalidOperationException ex)
        {
            Check(ex.Message.Contains("Missing at least one"),
                "full development period gate");
        }
        var lookahead=Source();
        lookahead.Add(new NQTimedBarV12(new DateTime(2023,1,1,9,30,0),
            new NQBarV11(100,102,98,101,100)));
        try
        {
            new NQNativeSignalCacheV14(lookahead,2000000);
            throw new Exception("missing 2023 out of sample guard");
        }
        catch(ArgumentException ex)
        {
            Check(ex.Message.Contains("held-out"),
                "OOS data never enter 2020–22 research cache");
        }
        // The full multi-generation economic research loop must choose
        // the IDENTICAL sequence of V11 genes, V9 scores and best candidate
        // when the callback is replaced by the cached V14 evaluator.
        int[] baseline={2,0,12,44,12,77,12,121,12,
            0,0,0,0,20,32,2,0,14,15,25};
        var ga=new NQEvolutionConfigV12{
            Population=24,Generations=3,Elites=3,Tournament=3,
            ImmigrantPercent=25,MutationPercent=20,Seed=20261106,
            MaxAttempts=10000
        };
        var referenceSearch=new NQNativeResearchPipelineV12(
            WithExtraHours(),baseline,ga,true,false).Run();
        var cachedSearch=new NQNativeCachedPipelineV14(
            WithExtraHours(),baseline,ga,true,false,4*1024*1024).Run();
        Check(referenceSearch.Evaluated.Count==cachedSearch.Evaluated.Count &&
              cachedSearch.Evaluated.Count==66,
              "multi-generation cached GA has identical number of runs");
        for(int i=0;i<referenceSearch.Evaluated.Count;i++)
            Check(referenceSearch.Evaluated[i].Genome.Canonical.RuntimeKey==
                  cachedSearch.Evaluated[i].Genome.Canonical.RuntimeKey &&
                  referenceSearch.Evaluated[i].Score==
                  cachedSearch.Evaluated[i].Score,
                  "cached and original genetic search must have identical "+
                  "selection order, genome identities and fitness");
        Check(referenceSearch.Best.Genome.Canonical.RuntimeKey==
              cachedSearch.Best.Genome.Canonical.RuntimeKey,
              "identical best strategy under cached V9 economic feedback");

        Console.WriteLine("NQ_V14_GENETIC_PIPELINE_PARITY generations="+
            cachedSearch.GenerationBest.Count+" unique="+
            cachedSearch.Evaluated.Count+" sameBest=TRUE");
        Console.WriteLine("NQ_V14_CACHE_PASS signalComparisons="+comparisons+
            " uniqueGenomes="+genomes.Count+" tables="+cache.Entries+
            " hits="+cache.CacheHits+" misses="+cache.CacheMisses+
            " signalBytes="+cache.UsedSignalBytes+
            " originalBars="+cache.SourceBars+
            " workingBars="+cache.WorkingBars+
            " atrBytes="+cache.UsedAtrBytes+
            " baselineMs="+uncachedMs+" cachedMs="+cachedMs+
            " tinyEvictions="+tiny.CacheEvictions);
        Console.WriteLine("NQ_V14_CACHE_PARITY_V12_ESTIMATE_ONLY_NO_REAL_NQ_DATA");
        return 0;
    }
}
