// V21 FEATURE MEMO is a pure candidate-scoring performance mechanism.
// Differential QA verifies SAME 1320 V19 condition semantics, especially
// 84 NEW formulas x 11 threshold rules. NO historical NQ market data.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V21MemoTest
{
    static void A(bool x,string msg)
    {if(!x)throw new Exception("NQ_V21_MEMO_FAIL "+msg);}
    static List<NQTimedBarV12> Synthetic()
    {
        var data=new List<NQTimedBarV12>();
        var random=new Random(20261106);
        double price=15000;
        for(int d=0;d<12;d++)
        {
            DateTime date=new DateTime(2020,6,1).AddDays(d);
            for(int i=0;i<210;i++)
            {
                double open=price;
                price+=0.42+Math.Sin((i+3*d)*0.15)*2.5+
                    (random.NextDouble()-0.5)*2.2;
                data.Add(new NQTimedBarV12(
                    date.AddHours(8).AddMinutes(i),
                    new NQBarV11(open,Math.Max(open,price)+0.75,
                        Math.Min(open,price)-0.75,price,20+random.Next(1400))));
            }
        }
        return data;
    }
    public static int Main()
    {
        var bars=Synthetic();
        var legacy=new NQNativeSignalCacheV14(bars,4*1024*1024,
            4*1024*1024,NQNativeConditionCatalogV19.Count,
            NQNativeExpandedResearchV19.Direction);
        int rth=legacy.RthBars;
        // Exactly 3 double feature tables, intentionally evicts while
        // all 84 families are exercised. No unbounded cache growth.
        var memo=new NQNativeFeatureMemoV21(legacy,8L*rth*3);
        A(memo.RthBars==rth,"same 09:30–11:27 signal chronology");
        int matched=0,variants=0;
        foreach(int period in new[]{6,12,24})
          for(int family=36;family<120;family++)
          {
              int sourceIndex=0;
              for(int d=0;d<12;d++)
              {
                  // 8:00 + 207 minutes = 11:27, last signal minute.
                  sourceIndex=d*210+207;
                  // All eleven formula variants from ONE feature table;
                  // the first build is reused by all other variants.
                  foreach(int rule in Enumerable.Range(0,11))
                  {
                      int type=family*11+rule;
                      int cached=memo.GetSignal(sourceIndex,type,period);
                      int reference=legacy.GetSignal(sourceIndex,type,period);
                      A(cached==reference,
                          "numeric feature memo semantic parity f="+
                           family+" period="+period+" rule="+rule);
                      matched++;
                      if(rule>0)variants++;
                  }
              }
              A(memo.UsedBytes<=memo.MaxBytes,
                "never exceed exact configured 3-table memory limit");
          }
        A(memo.FeatureBuilds>=84*3&&memo.Evictions>0,
          "all new families/periods calculated and bounded");
        A(memo.FeatureHits>=variants,
          "all 11 rules share underlying computed features");
        // V11/V18 delegation remains original byte-exact and never
        // attempts to evaluate historical rule 396+ as legacy V11.
        for(int type=0;type<396;type+=17)
        {
            int i=7*210+207;
            A(memo.GetSignal(i,type,12)==
              legacy.GetSignal(i,type,12),
              "original signal delegate parity "+type);
        }
        // Bad conditions/ranges are never quietly interpreted as
        // valid. Source-index valid but pre-RTH should be neutral.
        A(memo.GetSignal(0,400,12)==0,
          "outside RTH neutral without constructing futures");
        try
        {
            memo.GetSignal(5,1320,12);
            throw new Exception("INVALID_TYPE_1320_ACCEPTED");
        }
        catch(ArgumentOutOfRangeException){}
        // Backtest parity: V14 unmodified score + V21 numerical
        // family memo with same RTH compression and full ATR lookups.
        var example=new[]{
            2,44*11+1,12,104*11+3,12,112*11+1,
            12,85*11+1,12,0,0,0,0,20,32,2,0,14,15,25
        };
        var before=legacy.EvaluateExpanded(example,
            NQNativeExitCanonicalV19.Analyze);
        var after=memo.Evaluate(example);
        A(before.Valid&&after.Valid&&before.Score==after.Score&&
          before.Net==after.Net&&
          before.Trades.Count==after.Trades.Count &&
          before.Executed.Count==after.Executed.Count,
          "EXACT V12 economic score, trades and fill counts");
        for(int i=0;i<before.Executed.Count;i++)
        {
            var a=before.Executed[i];var b=after.Executed[i];
            A(a.EntryTime==b.EntryTime&&a.ExitTime==b.ExitTime&&
              a.EntryPrice==b.EntryPrice&&
              a.ExitPrice==b.ExitPrice&&
              a.RoundTripFeesUSD==b.RoundTripFeesUSD,
              "identical executed price/timing/fees roundtrip "+i);
        }
        Console.WriteLine("NQ_V21_FEATURE_MEMO_PASS comparisons="+matched+
            " familyPeriodTables="+memo.FeatureBuilds+
            " featureHits="+memo.FeatureHits+
            " evictions="+memo.Evictions+
            " peakPayloadBytes="+memo.UsedBytes+
            " originalSignalMisses="+legacy.CacheMisses+
            " economicTradeParity=TRUE");
        Console.WriteLine("SYNTHETIC_M1_MEMO_DIFFERENTIAL_ONLY");
        return 0;
    }
}
