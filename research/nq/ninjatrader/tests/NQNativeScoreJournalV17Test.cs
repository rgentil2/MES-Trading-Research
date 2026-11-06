// V17 restartable score-ledger QA. Synthetic objective on exact
// V11/V12 canonical genetic engine; verifies that extension from 4 to 9
// generations reuses all persisted evaluations without recomputing.
// Also proves changing the source checksum, scorer or genetic ranges
// refuses to reuse prior scores. NOT historical NQ profitability.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class V17JournalTest
{
    private static void A(bool yes,string why)
    {if(!yes)throw new Exception("NQ_V17_JOURNAL_FAIL "+why);}
    private static readonly int[] Baseline={
        2,0,12,44,12,77,12,121,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    private static NQEvolutionConfigV12 Cfg(int generations)
    {
        return new NQEvolutionConfigV12{
            Population=60,Generations=generations,Elites=6,
            Tournament=4,ImmigrantPercent=20,MutationPercent=18,
            Seed=20261106,MaxAttempts=20000,
            ResetAfterStagnantGenerations=4
        };
    }
    static double Objective(NQGenomeV11 g)
    {
        int[] x=g.Genes;
        return 10000-14*Math.Abs(x[0]-3)-
            2*Math.Abs(x[1]-40)-2*Math.Abs(x[3]-74)-
            3*Math.Abs(x[5]-89)-2*Math.Abs(x[13]-18);
    }
    static NQEvolutionSummaryV12 Run(string path,int generations,
        string source,int[] counter,Action<NQGenomeV11> before=null)
    {
        var ranges=NQEvolutionEngineV12.DefaultDomains(Baseline,true);
        var config=Cfg(generations);
        string signature=NQNativeScoreJournalV17.Fingerprint(
            config,ranges,"SYNTHETIC_V17_ORACLE_R1");
        using(var journal=new NQNativeScoreJournalV17(
            path,source,signature,8))
        {
            var result=new NQEvolutionEngineV12(ranges,config)
                .Run(g=>journal.Score(g,x=>{
                    before?.Invoke(x);
                    counter[0]++;
                    return Objective(x);
                }));
            A(result.Evaluated.Count==
                60+(generations-1)*(60-6),"unique evaluated count");
            A(journal.NewScored==counter[0],
                "persisted only newly evaluated scores");
            A(journal.Reused==result.Evaluated.Count-counter[0],
                "previously persisted fitness reused");
            return result;
        }
    }
    public static int Main()
    {
        string root=Path.Combine(Path.GetTempPath(),
            "NQ_V17_JOURNAL_"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        string file=Path.Combine(root,"scored.tsv");
        string aSha=new string('a',64),bSha=new string('b',64);
        try
        {
            int[] calls={0};
            var start=Run(file,4,aSha,calls);
            A(calls[0]==222,"60 + 3 x 54 initial actual scores");
            A(File.ReadLines(file).Count()==223,
                "header plus 222 validated rows");

            calls[0]=0;
            var extended=Run(file,9,aSha,calls);
            A(extended.Evaluated.Count==492&&calls[0]==270,
                "extend from 4 to 9 generations with 270 NEW callbacks");
            A(File.ReadLines(file).Count()==493,
                "append-only persistence has 492 unique results");

            calls[0]=0;
            var replay=Run(file,9,aSha,calls,x=>{
                throw new Exception("Persisted score must never be reevaluated");
            });
            A(calls[0]==0,"full 9-generation replay no new calculations");
            A(replay.Evaluated.Zip(extended.Evaluated,(a,b)=>
                a.Genome.Canonical.RuntimeKey==
                   b.Genome.Canonical.RuntimeKey&&a.Score==b.Score
                ).All(x=>x),"100% deterministic GA replay");
            A(start.Evaluated.Zip(replay.Evaluated,(a,b)=>
                a.Genome.Canonical.RuntimeKey==
                b.Genome.Canonical.RuntimeKey&&a.Score==b.Score
                ).All(x=>x),"frozen prefix unchanged on extension");

            // Mismatched development dataset cannot reuse prior score.
            try
            {Run(file,9,bSha,new[]{0});
             throw new Exception("LEAKED_TO_OTHER_DATASET");}
            catch(InvalidOperationException e)
            {A(e.Message.Contains("MISMATCH"),
                "source SHA protects score reuse");}

            var ranges=NQEvolutionEngineV12.DefaultDomains(Baseline,true);
            ranges[2]=new NQGeneRangeV11(6,18,3);
            string different=NQNativeScoreJournalV17.Fingerprint(
                Cfg(9),ranges,"SYNTHETIC_V17_ORACLE_R1");
            try
            {
                using(var wrong=new NQNativeScoreJournalV17(
                    file,aSha,different)){}
                throw new Exception("LEAKED_DIFFERENT_GENE_RANGE");
            }
            catch(InvalidOperationException e)
            {A(e.Message.Contains("MISMATCH"),
                "altered gene domain requires NEW journal");}

            string otherFitness=NQNativeScoreJournalV17.Fingerprint(
                Cfg(9),NQEvolutionEngineV12.DefaultDomains(
                    Baseline,true),"DIFFERENT_FITNESS_IMPLEMENTATION");
            try
            {
                using(var wrong=new NQNativeScoreJournalV17(
                    file,aSha,otherFitness)){}
                throw new Exception("LEAKED_DIFFERENT_SCORER");
            }
            catch(InvalidOperationException e)
            {A(e.Message.Contains("MISMATCH"),
                "new evaluation function invalidates persisted scores");}

            // Duplicate or tampered score row must fail closed.
            string[] all=File.ReadAllLines(file);
            File.AppendAllText(file,all[1]+"\n");
            try
            {
                using(var damaged=new NQNativeScoreJournalV17(
                    file,aSha,NQNativeScoreJournalV17.Fingerprint(Cfg(9),
                      NQEvolutionEngineV12.DefaultDomains(
                          Baseline,true),"SYNTHETIC_V17_ORACLE_R1"))){}
                throw new Exception("DUPLICATE_ROW_WAS_ACCEPTED");
            }
            catch(InvalidDataException e)
            {A(e.Message.Contains("Duplicate"),
                "duplicate journal records rejected");}
            File.WriteAllLines(file,all);
            string[] corrupt=(string[])all.Clone();
            corrupt[3]+="TRAILING_GARBAGE";
            File.WriteAllLines(file,corrupt);
            try
            {
                using(var damaged=new NQNativeScoreJournalV17(
                    file,aSha,NQNativeScoreJournalV17.Fingerprint(Cfg(9),
                      NQEvolutionEngineV12.DefaultDomains(
                        Baseline,true),"SYNTHETIC_V17_ORACLE_R1"))){}
                throw new Exception("TRUNCATED_OR_CORRUPTED_ACCEPTED");
            }
            catch(InvalidDataException)
            { /* fail-closed */ }

            Console.WriteLine("NQ_V17_JOURNAL_PASS initial=222 "+
                "reused=222 additional=270 total=492 "+
                "replayScoreCallbacks=0 identicalSequence=TRUE "+
                "sourceGuard=TRUE scorerGuard=TRUE rangeGuard=TRUE "+
                "duplicateCorruptionGuard=TRUE");
            Console.WriteLine("DETERMINISTIC_SYNTHETIC_FITNESS_LEDGER_ONLY");
            return 0;
        }
        finally
        {
            Directory.Delete(root,true);
        }
    }
}
