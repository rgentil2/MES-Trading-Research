// V16 full headless research entrypoint test on a synthetic 36-month
// M1 development sequence. Its purpose is fail-closed gate wiring,
// NOT to demonstrate actual NQ economic edge or live NT8 performance.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class V16ResearchRunnerTest
{
    static void A(bool yes,string msg)
    {if(!yes)throw new Exception("NQ_V16_RUNNER_FAIL "+msg);}
    static NQDataLoadV16 Development(bool incomplete=false)
    {
        var rows=new List<NQTimedBarV12>(65000);
        int[] full=new int[36];
        for(int y=2020;y<=2022;y++)
            for(int m=1;m<=12;m++)
                for(int d=1;d<=29;d+=2)
                {
                    if(incomplete&&y==2021&&m==3&&d==29)continue;
                    DateTime start=new DateTime(y,m,d,9,30,0);
                    for(int i=0;i<120;i++)
                    {
                        double price=15000+i*0.50;
                        rows.Add(new NQTimedBarV12(start.AddMinutes(i),
                            new NQBarV11(price,price+0.50,
                                price-0.50,price,200)));
                    }
                    full[(y-2020)*12+m-1]++;
                }
        return new NQDataLoadV16(new NQDataManifestV16(
            NQDataPartitionV16.Development2020_2022,
            "NQ CONTINUOUS","BACKADJUSTED_UNVERIFIED",
            new string('b',64),new DateTime(2020,1,1),
            new DateTime(2022,12,31),new DateTime(2020,1,1),
            new DateTime(2022,12,31),rows.Count,rows.Count,
            full.Sum(),full),rows.AsReadOnly());
    }
    static NQResearchConfigV16 Config()
    {
        return new NQResearchConfigV16{
            Genetic=new NQEvolutionConfigV12{
                Population=12,Generations=2,Elites=2,Tournament=3,
                ImmigrantPercent=25,MutationPercent=18,
                Seed=20261106,MaxAttempts=10000
            },
            CandidateAuditLimit=10,
            SignalCacheBytes=16*1024*1024,
            MinimumFullDaysPerMonth=15,
            WalkForward=new NQWalkForwardConfigV15{
                MinimumFullSessionsPerMonth=15,
                Evolution=new NQEvolutionConfigV12{
                    Population=12,Generations=2,Elites=2,
                    Tournament=3,Seed=20261106,MaxAttempts=10000
                }
            },
            FinalCutoffExclusive=new DateTime(2026,11,1)
        };
    }
    static int[] Genes()
    {return new[]{1,0,6,44,12,77,12,121,12,
        0,0,0,0,20,32,2,0,14,15,25};}
    public static int Main()
    {
        var data=Development();
        A(data.Manifest.FullSessionsByMonth.All(x=>x==15),
            "36 months x 15 complete 9:30-11:29 sessions");
        var cfg=Config();
        var one=NQNativeResearchRunnerV16.Run(data,Genes(),cfg);
        A(one.Completed && one.Genetic!=null &&
          one.GeneticEvaluated==22 &&
          one.RobustnessChecked==10 &&
          one.RobustnessPassed<=10,
          "actual V14 GA to V13 risk-audit executable chain");
        A(!one.HasFrozenCandidates &&
          one.FrozenCampaign==null &&
          one.Reason!="FROZEN_DEVELOPMENT_ONLY_READY_FOR_EXTERNAL",
          "sparse synthetic candidate set fails closed, no fake portfolio");
        A(one.RobustCandidateKeys.Count==one.RobustnessPassed,
          "only provisional risk passes appear in reviewed pool");
        A(one.Genetic.Evaluated.All(x=>
          x.Genome.Canonical.RuntimeKey!=null),
          "all GA identities frozen by canonical search");

        var repeated=NQNativeResearchRunnerV16.Run(
            Development(),Genes(),Config());
        A(repeated.Genetic.Evaluated.Count==one.GeneticEvaluated &&
          repeated.Genetic.Evaluated.Zip(one.Genetic.Evaluated,
            (a,b)=>a.Genome.Canonical.RuntimeKey==
              b.Genome.Canonical.RuntimeKey&&a.Score==b.Score).All(x=>x),
          "seeded GA and original economics repeat exactly");

        var insufficient=NQNativeResearchRunnerV16.Run(
            Development(true),Genes(),Config());
        A(!insufficient.Completed&&
          insufficient.Reason=="DEVELOPMENT_SOURCE_INCOMPLETE" &&
          !insufficient.HasFrozenCandidates,
          "one month with 14/15 sessions fails before GA starts");

        var notDev=new NQDataLoadV16(new NQDataManifestV16(
            NQDataPartitionV16.ExternalValidation2023_2024,
            "NQ CONTINUOUS","BACKADJUSTED_UNVERIFIED","abc",
            new DateTime(2023,1,1),new DateTime(2024,12,31),
            new DateTime(2023,1,1),new DateTime(2024,12,31),
            1,1,0,new int[24]),new List<NQTimedBarV12>());
        var leak=NQNativeResearchRunnerV16.Run(
            notDev,Genes(),Config());
        A(!leak.Completed&&!leak.HasFrozenCandidates &&
          leak.Reason=="INVALID_DEVELOPMENT_INPUT",
          "external held-out input cannot enter the GA research runner");

        Console.WriteLine("NQ_V16_RESEARCH_RUNNER_PASS "+
            "geneticUnique="+one.GeneticEvaluated+
            " auditCount="+one.RobustnessChecked+
            " robustPass="+one.RobustnessPassed+
            " finalResult="+one.Reason+
            " withheldFutureData=TRUE");
        Console.WriteLine("SYNTHETIC_DEVELOPMENT_ONLY_NO_PROFITABLE_REAL_NQ_CANDIDATES");
        return 0;
    }
}
