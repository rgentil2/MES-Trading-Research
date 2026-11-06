// V21 durable full-economic GA: 90 ACTUAL complete V12 M1
// backtests of 1320-condition genomes, then zero-repeat source-locked
// deterministic restart. Compare ordinary V14 and V21 memo economic
// results, rank/trade/fill/fees and corruption/parameter guards.
// Source is SYNTHETIC completed M1, NOT real NQ DEC2026 data.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V21BulkTest
{
    static void A(bool ok,string why)
    {if(!ok)throw new Exception("NQ_V21_BULK_FAIL "+why);}
    static readonly int[] Base={
        2,396,12,789,12,999,12,1319,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    static NQEvolutionConfigV12 Config()
    {
        return new NQEvolutionConfigV12{
            Population=30,Generations=3,Elites=4,Tournament=3,
            ImmigrantPercent=20,MutationPercent=18,
            Seed=20261106,MaxAttempts=10000,
            ResetAfterStagnantGenerations=3
        };
    }
    static List<NQTimedBarV12> Bars()
    {
        var source=new List<NQTimedBarV12>();
        var rng=new Random(20261106);
        double price=15000;
        for(int d=0;d<14;d++)
        {
            DateTime day=new DateTime(2020,7,1).AddDays(d);
            for(int i=0;i<210;i++)
            {
                double open=price;
                price+=0.5+Math.Sin((i+9*d)*0.12)*2.1+
                    (rng.NextDouble()-0.5)*2.2;
                source.Add(new NQTimedBarV12(
                    day.AddHours(8).AddMinutes(i),
                    new NQBarV11(open,Math.Max(open,price)+0.5,
                        Math.Min(open,price)-0.5,price,100+rng.Next(700))));
            }
        }
        return source;
    }
    public static int Main()
    {
        var bars=Bars();
        string root=Path.Combine(Path.GetTempPath(),
            "NQV21_"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        string ledger=Path.Combine(root,"memo.tsv"),
            ranked=Path.Combine(root,"rank.tsv"),
            fills=Path.Combine(root,"trades.tsv"),
            baseline=Path.Combine(root,"baseline.tsv"),
            baseRank=Path.Combine(root,"baseline_rank.tsv"),
            baseFills=Path.Combine(root,"baseline_fills.tsv");
        string sha=new string('a',64);
        try
        {
            var direct=NQNativeBulkEconomicV21.Run(
                bars,Base,Config(),sha,baseline,
                baseRank,baseFills,5,8*1024*1024,
                8*1024*1024,false);
            var first=NQNativeBulkEconomicV21.Run(
                bars,Base,Config(),sha,ledger,
                ranked,fills,5,8*1024*1024,
                8*1024*1024,true);
            const int expected=30+2*(30-4);
            A(expected==82&&first.Unique==expected &&
              first.NewEconomicBacktests==expected &&
              first.ReusedEconomicBacktests==0,
              "82 unique FULL M1 economic GA backtests");
            A(direct.Unique==expected&&
              direct.NewEconomicBacktests==expected,
              "same V12 legacy full economic backtests run");
            A(first.Evolution.Evaluated.Zip(
                direct.Evolution.Evaluated,(a,b)=>
                  a.Score==b.Score&&
                  a.Genome.Canonical.RuntimeKey==
                    b.Genome.Canonical.RuntimeKey).All(x=>x),
              "memo V21 economic GA scores bitwise equal to original V14");
            A(first.Top.Count==5&&
              first.FinalistBacktests==5,
              "5 finalists fully re-evaluated for actual fill receipts");
            A(first.FeatureBuilds>0 &&
              first.FeatureMemoryBytes<=8*1024*1024,
              "bounded V19 family memo was invoked");
            var rows=File.ReadAllLines(ledger);
            A(rows.Length==expected+1,
              "ledger has 1 SHA header + 82 numeric economic results");
            A(File.ReadAllLines(ranked).Length==6,
              "top five structured economic leaderboard rows");
            A(File.ReadAllLines(fills).Length>=1,
              "top-five full trade receipt report created");

            // Replay from disk must not recalculate any GA economic
            // backtest, except the 5 finalist audit receipts (documented).
            var replay=NQNativeBulkEconomicV21.Run(
                bars,Base,Config(),sha,ledger,
                ranked,fills,5,8*1024*1024,
                8*1024*1024,true);
            A(replay.Unique==expected&&
              replay.NewEconomicBacktests==0&&
              replay.ReusedEconomicBacktests==expected,
              "source-locked GA scored 82 without 1 new full evaluation");
            A(replay.FinalistBacktests==5&&
              File.ReadAllLines(ledger).Length==expected+1,
              "on restart ONLY bounded 5 finalists replayed");
            A(first.Evolution.Evaluated.Zip(
                replay.Evolution.Evaluated,(a,b)=>
                  a.Score==b.Score&&
                  a.Genome.Canonical.RuntimeKey==
                    b.Genome.Canonical.RuntimeKey).All(x=>x),
              "same deterministic 82-genome score order on resume");
            A(first.Top.Zip(replay.Top,(a,b)=>
                a.Canonical==b.Canonical&&
                a.Score==b.Score&&a.Trades==b.Trades&&
                a.Net==b.Net&&a.ProfitFactor==b.ProfitFactor).All(x=>x),
              "economic rankings fully deterministic");

            // Controlled extension beyond original generation count:
            // V17/V21 fingerprint intentionally excludes generations.
            var longer=Config();longer.Generations=4;
            var ext=NQNativeBulkEconomicV21.Run(
                bars,Base,longer,sha,ledger,ranked,fills,5,
                8*1024*1024,8*1024*1024,true);
            A(ext.Unique==108&&ext.ReusedEconomicBacktests==expected&&
              ext.NewEconomicBacktests==26,
              "extend 3 to 4 generations without reevaluating first 82");
            var again=NQNativeBulkEconomicV21.Run(
                bars,Base,longer,sha,ledger,ranked,fills,5,
                8*1024*1024,8*1024*1024,true);
            A(again.NewEconomicBacktests==0 &&
              again.ReusedEconomicBacktests==108,
              "extended ledger 108 GA candidates perfectly replayed");
            try
            {
                NQNativeBulkEconomicV21.Run(bars,Base,Config(),
                    new string('b',64),ledger,ranked,fills,5,
                    8*1024*1024,8*1024*1024,true);
                throw new Exception("SOURCE_SHA_LEAK");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("MISMATCH"),
                "new data fingerprint rejects stale economic statistics");}
            var other=Config();other.Seed++;
            try
            {
                NQNativeBulkEconomicV21.Run(bars,Base,other,sha,
                    ledger,ranked,fills,5,8*1024*1024,
                    8*1024*1024,true);
                throw new Exception("SEED_SETTINGS_LEAK");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("MISMATCH"),
                "changed genetic search identity rejects stale ledger");}
            string[] corrupt=File.ReadAllLines(ledger);
            corrupt[3]+="CORRUPTION";
            File.WriteAllLines(ledger,corrupt);
            try
            {
                using(var invalid=new NQNativeEconomicLedgerV21(
                    ledger,sha,NQNativeEconomicLedgerV21.Fingerprint(
                        Config(),Base,true))){}
                throw new Exception("CORRUPT_ECON_LEDGER_ACCEPTED");
            }
            catch(InvalidDataException ex)
            {A(ex.Message.Contains("CHECKSUM"),
                "corrupted row rejected rather than silently repaired");}

            Console.WriteLine("NQ_V21_BULK_ECONOMIC_PASS "+
                "uniqueCompleteV12Backtests="+expected+
                " directParity="+direct.Unique+
                " resumeFresh="+replay.NewEconomicBacktests+
                " resumeReused="+replay.ReusedEconomicBacktests+
                " extensionFresh="+ext.NewEconomicBacktests+
                " extensionReused="+ext.ReusedEconomicBacktests+
                " allCandidatesWithNetPFDD="+again.Unique+
                " finalistsWithDetailedFills="+again.FinalistBacktests+
                " memoFirstMs="+first.ElapsedMilliseconds+
                " v14FirstMs="+direct.ElapsedMilliseconds+
                " memoFeatureBuilds="+first.FeatureBuilds+
                " sourceAndConfigGuard=TRUE corruptionGuard=TRUE");
            Console.WriteLine("V21_M1_IS_SYNTHETIC; NO_100K_REAL_NQ_ECONOMIC_BACKTEST_PROVEN");
            return 0;
        }
        finally{Directory.Delete(root,true);}
    }
}
