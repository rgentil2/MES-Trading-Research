// S0.84 V23 complete one-command generator and deterministic run package.
// This suite deliberately uses 2020–22 SYNTHETIC M1. It cannot
// establish a profitable NQ DEC2026 strategy or native NT8 fills.
using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using NinjaTrader.NinjaScript.Strategies;
internal static class V23CompleteGeneratorTest
{
    private static void A(bool good,string why)
    {if(!good)throw new Exception("NQ_V23_COMPLETE_FAIL "+why);}
    private static readonly int[] Base={
        2,396,12,789,12,999,12,1319,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    private static readonly int[] Days={1,5,9,13,17,21,25,28};
    private static NQDataLoadV16 Development(bool missing=false,
        bool perturbLate=false)
    {
        var rows=new List<NQTimedBarV12>(64000);
        var monthCounts=new int[36];
        double last=15000;
        var rng=new Random(20261106);
        for(int y=2020;y<=2022;y++)
          for(int m=1;m<=12;m++)
            for(int di=0;di<Days.Length;di++)
            {
                int day=Days[di];
                if(missing&&y==2021&&m==4&&day==28)continue;
                DateTime date=new DateTime(y,m,day);
                for(int minute=0;minute<210;minute++)
                {
                    double op=last;
                    double phase=(minute+4*m+di*7)*0.14;
                    double drift=(y==2020?0.5:y==2021?-0.4:0.6)+
                        Math.Sin(phase)*1.4+(rng.NextDouble()-0.5)*1.5;
                    if(perturbLate&&y==2022&&m>=7)
                        drift=-2+Math.Sin(phase)*1.2;
                    last=Math.Max(1500,last+drift);
                    rows.Add(new NQTimedBarV12(
                        date.AddHours(8).AddMinutes(minute),
                        new NQBarV11(op,Math.Max(op,last)+0.6,
                            Math.Min(op,last)-0.6,last,200+minute%73)));
                }
                monthCounts[(y-2020)*12+m-1]++;
            }
        var manifest=new NQDataManifestV16(
            NQDataPartitionV16.Development2020_2022,
            "NQ DEC2026","NT8_SERIES_VISIBLE_2020_22_USER_CONFIRMED",
            new string('a',64),new DateTime(2020,1,1),
            new DateTime(2022,12,31),new DateTime(2020,1,1),
            new DateTime(2022,12,31),rows.Count,rows.Count,
            monthCounts.Sum(),monthCounts);
        return new NQDataLoadV16(manifest,rows.AsReadOnly());
    }
    private static NQEvolutionConfigV12 Genetic(int seed=20261106)
    {
        return new NQEvolutionConfigV12{
            Population=12,Generations=2,Elites=2,
            Tournament=3,Seed=seed,MaxAttempts=10000,
            ImmigrantPercent=20,MutationPercent=18
        };
    }
    private static NQWalkForwardConfigV15 WF()
    {
        return new NQWalkForwardConfigV15{
            MinimumFullSessionsPerMonth=8,
            SignalCacheBytes=32L*1024*1024,
            AtrCacheBytes=32L*1024*1024,
            Evolution=Genetic()
        };
    }
    private static NQResearchConfigV16 Config()
    {
        return new NQResearchConfigV16{
            Genetic=Genetic(),CandidateAuditLimit=10,
            SignalCacheBytes=32L*1024*1024,
            MinimumFullDaysPerMonth=8,
            WalkForward=WF(),
            FinalCutoffExclusive=new DateTime(2026,11,1),
            Robustness=new NQRobustnessConfigV13{
                BootstrapPaths=100,BlockLengthTrades=8,
                Seed=20261106,BaseAllInCostPerTradeUSD=24.68,
                CostMultiplier=1.5,MaxBootstrapP95ClosedDDUSD=2000
            }
        };
    }
    private static NQGeneratorSettingsV23 Settings(
        NQDataLoadV16 data,string output)
    {
        return new NQGeneratorSettingsV23{
            InputPath="SYNTHETIC_2020_22_M1_ONLY",
            OutputDirectory=output,
            Instrument=data.Manifest.Instrument,
            ContractPolicy=data.Manifest.ContractPolicy,
            SourceRevision=NQNativeReproducibilityV23.Version,
            MinimumFullSessionsPerMonth=8,
            Research=Config(),BaselineGenes=(int[])Base.Clone(),
            RankingCount=5,FeatureCacheBytes=16*1024*1024
        };
    }
    private static int Lines(string dir,string file)
    {return File.ReadLines(Path.Combine(dir,file)).Count();}
    public static int Main()
    {
        string dir=Path.Combine(Path.GetTempPath(),
            "NQV23_PACKAGE_"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        try
        {
            var data=Development();
            var cfg=Settings(data,dir);
            string originalLock=NQNativeReproducibilityV23.LockText(
                cfg,data);
            A(originalLock.Contains("features=120")&&
              originalLock.Contains("conditions=1320")&&
              originalLock.Contains("outOfSampleEvaluated=false"),
              "V23 locked development-only versioned 120/1320 catalog");
            var first=NQNativeCompleteGeneratorV23.Run(data,cfg);
            NQNativeCompleteGeneratorV23.Verify(dir);
            A(first.Completed&&
              first.Generated==22&&first.Audited==10&&
              first.IndividualPassed==5&&
              first.FreshBacktests==22&&first.ReusedBacktests==0&&
              first.FreezeCount==0&&!first.HasFrozenCandidates&&
              first.Reason=="PORTFOLIO_RISK_OR_DIVERSITY_REJECT",
              "single execution traces 22 economic genomes, 10 auditable"+
              " candidates, 5 individually acceptable, correct 3-5 risk reject");
            A(Lines(dir,"candidates_full.tsv")==23&&
              Lines(dir,"rejected_candidates.tsv")==23&&
              Lines(dir,"robustness_audits.tsv")==11&&
              Lines(dir,"annual_development.tsv")==31&&
              Lines(dir,"monthly_development.tsv")==361&&
              Lines(dir,"definitive_parameters.tsv")==1&&
              Lines(dir,"portfolio_decision.tsv")==2&&
              Lines(dir,"walkforward.tsv")==1,
              "complete ranking/rejection/year/month/portfolio/WF reports"+
              " even with NO qualified frozen portfolio");
            A(Lines(dir,"audited_trades.tsv")>100&&
              Lines(dir,"finalist_trades.tsv")>1,
              "full audited M1 entry/exit price, MAE/MFE, fee receipts");
            A(File.ReadAllText(Path.Combine(dir,"run_summary.txt"))
                .Contains("noApprovedPortfolioIsNotFailureOfSoftware=true"),
              "reject does not claim false profitability");
            A(File.ReadAllText(Path.Combine(dir,"run_summary.txt"))
                .Contains("externalOosOpened=false")&&
              File.ReadAllText(Path.Combine(dir,"run_summary.txt"))
                .Contains("finalOosOpened=false"),
              "2023+ OOS remains totally unopened");

            // Positive *serialization only* test for 3 and 5
            // externally qualified FIXTURE genomes. No real GA result
            // in this test passed portfolio risk, so no positive actual
            // V23 frozen campaign is being claimed.
            string paramsFixture=Path.Combine(Path.GetTempPath(),
                "NQ_V23_FROZEN_GENE_FIXTURE_"+
                Guid.NewGuid().ToString("N")+".tsv");
            try
            {
                var five=new List<NQFrozenCandidateV16>();
                for(int k=0;k<5;k++)
                {
                    int[] g=(int[])Base.Clone();
                    g[1]=396+k*11;
                    g[3]=789+k*11;
                    five.Add(new NQFrozenCandidateV16("FIXTURE_"+k,g,
                        NQNativeExitCanonicalV19.Analyze));
                }
                NQNativeCompleteGeneratorV23.WriteFrozenParameterFile(
                    paramsFixture,five.Take(3).ToList());
                A(File.ReadAllLines(paramsFixture).Length==61 &&
                  File.ReadAllText(paramsFixture).Contains("stopTicks") &&
                  File.ReadAllText(paramsFixture).Contains("signalType"),
                  "3 frozen fixture genomes export exactly 60 parameters");
                NQNativeCompleteGeneratorV23.WriteFrozenParameterFile(
                    paramsFixture,five);
                A(File.ReadAllLines(paramsFixture).Length==101&&
                  File.ReadAllText(paramsFixture).Contains(
                    NQNativeConditionCatalogV19.Name(396)),
                  "5 frozen fixture genomes export 100 exact signal/exit parameters");
            }
            finally
            {if(File.Exists(paramsFixture))File.Delete(paramsFixture);}
            string oldPackage=first.PackageSHA256;
            var resumed=NQNativeCompleteGeneratorV23.Run(data,cfg);
            NQNativeCompleteGeneratorV23.Verify(dir);
            A(resumed.Generated==22&&resumed.Audited==10&&
              resumed.FreshBacktests==0&&resumed.ReusedBacktests==22,
              "second identical run recovers 22 scores from disk, no new backtests");
            A(resumed.PackageSHA256==oldPackage &&
              File.ReadAllText(Path.Combine(dir,"campaign.lock"))==
                originalLock,
              "resumed source/parameters/annual/rejections are BYTE-IDENTICAL");
            A(resumed.Research.Genetic.Evaluated.Zip(
                first.Research.Genetic.Evaluated,(a,b)=>
                   a.Score==b.Score&&
                   a.Genome.Canonical.RuntimeKey==
                      b.Genome.Canonical.RuntimeKey).All(x=>x),
              "same deterministic genetic search ranking after resume");

            // The fixed V23 risk contract may be TIGHTENED but never
            // silently relaxed, including cutoff / annual robustness.
            cfg.Research.Robustness.CostMultiplier=1.0;
            try{cfg.Validate();throw new Exception("V23_WEAK_COST_ACCEPTED");}
            catch(ArgumentException ex)
            {A(ex.Message.Contains("WEAKEN"),
                "less than 1.5x cost stress fails config");}
            cfg.Research.Robustness.CostMultiplier=1.5;
            cfg.Audit.MinimumPositiveDevelopmentYears=2;
            try{cfg.Validate();throw new Exception("V23_WEAK_YEAR_ACCEPTED");}
            catch(ArgumentException ex)
            {A(ex.Message.Contains("WEAKEN"),
                "less than all three development years fails config");}
            cfg.Audit.MinimumPositiveDevelopmentYears=3;
            cfg.Research.FinalCutoffExclusive=new DateTime(2027,1,1);
            try{cfg.Validate();throw new Exception("V23_CHANGED_CUTOFF_ACCEPTED");}
            catch(ArgumentException ex)
            {A(ex.Message.Contains("WEAKEN"),
                "frozen 2026-11-01 OOS cutoff cannot drift");}
            cfg.Research.FinalCutoffExclusive=new DateTime(2026,11,1);

            cfg.RankingCount=6;
            try
            {
                NQNativeCompleteGeneratorV23.Run(data,cfg);
                throw new Exception("V23_ACCEPTED_CHANGED_CONFIG");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("MISMATCH"),
                "config drift cannot overwrite prior frozen research package");}
            cfg.RankingCount=5;
            try
            {
                NQNativeCompleteGeneratorV23.Run(
                    Development(false,true),cfg);
                throw new Exception("V23_ACCEPTED_CHANGED_SOURCE_BARS");
            }
            catch(InvalidOperationException ex)
            {A(ex.Message.Contains("MISMATCH"),
                "same manifest raw SHA BUT changed OHLCV content rejected");}
            var annual=Path.Combine(dir,"annual_development.tsv");
            File.AppendAllText(annual,"CORRUPT");
            try
            {
                NQNativeCompleteGeneratorV23.Verify(dir);
                throw new Exception("V23_CORRUPT_FILE_ACCEPTED");
            }
            catch(InvalidDataException ex)
            {A(ex.Message.Contains("MODIFIED"),
                "per-artifact SHA256 detects tampered annual results");}
            var repaired=NQNativeCompleteGeneratorV23.Run(data,cfg);
            NQNativeCompleteGeneratorV23.Verify(dir);
            A(repaired.PackageSHA256==oldPackage&&
              repaired.ReusedBacktests==22,
              "deterministic report repair does not recalculate 22 backtests");
            A(first.ArtifactNames.Contains("economics_ledger.tsv")&&
              first.ArtifactNames.Contains("monthly_development.tsv")&&
              first.ArtifactNames.Contains("audited_trades.tsv")&&
              first.ArtifactNames.Contains("definitive_parameters.tsv")&&
              first.ArtifactNames.Contains("artifacts.sha256"),
              "reproducible package includes economy, all audited trading,"+
              " yearly/monthly, freeze params and hashes");
            Console.WriteLine("NQ_V23_COMPLETE_GENERATOR_PASS "+
                "version=V23_FIXED_SCOPE scored="+first.Generated+
                " audited="+first.Audited+
                " individualPass="+first.IndividualPassed+
                " portfolio=REJECTED"+
                " allCandidateRankRows="+(Lines(dir,"candidates_full.tsv")-1)+
                " monthlyMetricsRows="+(Lines(dir,"monthly_development.tsv")-1)+
                " annualMetricsRows="+(Lines(dir,"annual_development.tsv")-1)+
                " artifacts="+first.ArtifactNames.Count+
                " newBacktestsOnResume="+resumed.FreshBacktests+
                " outputByteExactReplay=TRUE"+
                " changedConfigGuard=TRUE changedBarsGuard=TRUE"+
                " checksumTamperGuard=TRUE frozenParamFixture3And5=TRUE"+
                " fixedRiskContract=TRUE externalFinalUnopened=TRUE");
            Console.WriteLine("SOURCE_IS_SYNTHETIC_2020_2022_NO_NQ_DEC2026_PROFIT_CLAIMS");
            return 0;
        }
        finally{Directory.Delete(dir,true);}
    }
}
