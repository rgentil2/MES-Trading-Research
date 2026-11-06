// S0.85 V24 *performance-only* runner. Reuses exactly the 42
// pinned V23 C# modules, adds precompiled signals and long-horizon
// full V12 economic GA benchmarks. It is NOT the V23 report system,
// and is NOT the V25 native NinjaTrader integration.
using System;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;
using NinjaTrader.NinjaScript.Strategies;
internal static class NQNativeV24Console
{
    static readonly CultureInfo I=CultureInfo.InvariantCulture;
    static readonly JsonSerializerOptions Json=new JsonSerializerOptions{
        IncludeFields=true,PropertyNameCaseInsensitive=false
    };
    static void Help()
    {
        Console.WriteLine("V24 ONLY: full-M1 economic long-horizon scaling.");
        Console.WriteLine("  --bench-synthetic36 <dir> <population> <generations>");
        Console.WriteLine("  --run-development <V23-search-config.json>");
        Console.WriteLine("  --version");
        Console.WriteLine("This does not validate NQ edge or invoke NinjaTrader.");
    }
    static int Positive(string raw,int max)
    {
        int x;
        if(!Int32.TryParse(raw,out x)||x<1||x>max)
            throw new ArgumentException("V24_INVALID_POSITIVE_COUNT");
        return x;
    }
    static void Output(NQEconomicScaleResultV24 r,
        string destination,string kind)
    {
        var rows=new[]{
            "V24_ECONOMIC_M1_SCALE_PROFILE\t"+kind,
            "sourceBars\t"+r.SourceBars,
            "workingRthBars\t"+r.WorkingBars,
            "completeWeekdaySessions\t"+r.CompleteSessions,
            "uniqueEconomicGenomes\t"+r.UniqueGenomes,
            "newV12M1Backtests\t"+r.NewEconomicBacktests,
            "reusedJournalScores\t"+r.ReusedGenomes,
            "millisecondElapsed\t"+r.ElapsedMilliseconds,
            "newFullBacktestsPerSecond\t"+
                r.FullBacktestsPerSecond.ToString("R",I),
            "millionRthBarVisitsPerSecond\t"+
                r.MillionBarVisitsPerSecond.ToString("R",I),
            "numericFeatureTablesBuilt\t"+r.NumericTablesCreated,
            "numericFeatureTableReuses\t"+r.NumericTableReuses,
            "numericFeatureTableEvictions\t"+r.TableEvictions,
            "numericFeaturePayloadBytes\t"+r.FeaturePayloadBytes,
            "signalCachePayloadBytes\t"+r.SignalPayloadBytes,
            "atrPayloadBytes\t"+r.AtrPayloadBytes,
            "processPeakWorkingSetBytes\t"+r.ProcessPeakWorkingSetBytes,
            "endManagedHeapBytes\t"+r.MaxObservedManagedBytes,
            "sourceBarsSHA256\t"+r.SourceSeriesSHA256,
            "economicConfigSHA256\t"+r.ConfigSHA256,
            "syntheticScoreIsNotNQProfitability\ttrue",
            "doesNotOpen2023PlusOOS\ttrue"
        };
        string target=Path.Combine(destination,"v24_scale_profile.tsv");
        File.WriteAllLines(target,rows,new UTF8Encoding(false));
        Console.WriteLine("NQ_V24_SCALE_ECONOMIC "+
            "source="+kind+
            " fullBacktests="+r.NewEconomicBacktests+
            " journalReused="+r.ReusedGenomes+
            " workingBars="+r.WorkingBars+
            " seconds="+
                (r.ElapsedMilliseconds/1000.0).ToString("F3",I)+
            " backtestsPerSecond="+
                r.FullBacktestsPerSecond.ToString("F4",I)+
            " featurePayloadMiB="+
                (r.FeaturePayloadBytes/1048576.0).ToString("F2",I)+
            " maxWorkingSetMiB="+
                (r.ProcessPeakWorkingSetBytes/1048576.0).ToString("F2",I));
    }
    static NQEvolutionConfigV12 Genetic(int population,int generations)
    {
        var value=new NQEvolutionConfigV12{
            Population=population,
            Generations=generations,
            Elites=Math.Max(1,Math.Min(population-1,population/12)),
            Tournament=Math.Min(5,population),
            Seed=20261106,
            MaxAttempts=Math.Max(population*generations*12,20000),
            ImmigrantPercent=24,
            MutationPercent=18,
            ResetAfterStagnantGenerations=7
        };
        value.Validate();
        return value;
    }
    public static int Main(string[] args)
    {
        try
        {
            if(args.Length==1&&args[0]=="--version")
            {
                Console.WriteLine(NQNativeEconomicScaleV24.EngineVersion);
                return 0;
            }
            NQDataLoadV16 data;
            NQEvolutionConfigV12 ga;
            int[] genes;
            string destination,sourceDescription;
            if(args.Length==4&&args[0]=="--bench-synthetic36")
            {
                int population=Positive(args[2],10000);
                int generations=Positive(args[3],10000);
                data=NQNativeSynthetic36V24.Build();
                ga=Genetic(population,generations);
                genes=new NQGeneratorSettingsV23().BaselineGenes;
                destination=Path.GetFullPath(args[1]);
                sourceDescription="SYNTHETIC_36_MONTH_WEEKDAYS";
            }
            else if(args.Length==2&&args[0]=="--run-development")
            {
                string path=Path.GetFullPath(args[1]);
                var cfg=JsonSerializer.Deserialize<NQGeneratorSettingsV23>(
                    File.ReadAllText(path),Json);
                if(cfg==null)
                    throw new InvalidDataException("V24_NULL_V23_SETTINGS");
                string folder=Path.GetDirectoryName(path);
                if(!Path.IsPathRooted(cfg.InputPath))
                    cfg.InputPath=Path.GetFullPath(
                        Path.Combine(folder,cfg.InputPath));
                if(!Path.IsPathRooted(cfg.OutputDirectory))
                    cfg.OutputDirectory=Path.GetFullPath(
                        Path.Combine(folder,cfg.OutputDirectory));
                cfg.Validate();
                using(var raw=File.OpenRead(cfg.InputPath))
                    data=NQNativeDataLoaderV16.Load(
                        raw,NQDataPartitionV16.Development2020_2022,
                        cfg.Instrument,cfg.ContractPolicy,
                        Math.Max(15,cfg.MinimumFullSessionsPerMonth));
                ga=cfg.Research.Genetic;genes=cfg.BaselineGenes;
                destination=Path.Combine(cfg.OutputDirectory,
                    "V24_LARGE_ECONOMIC_SCALE_ONLY");
                sourceDescription="USER_SUPPLIED_DEV_2020_22_NOT_YET_VERIFIED_NT8";
            }
            else{Help();return 2;}
            Directory.CreateDirectory(destination);
            var result=NQNativeEconomicScaleV24.Run(
                data,genes,ga,
                Path.Combine(destination,"v24_economics_ledger.tsv"),
                Path.Combine(destination,"v24_top_ranking.tsv"),
                20,128L*1024*1024,256L*1024*1024);
            Output(result,destination,sourceDescription);
            Console.WriteLine("V24_REPORTS="+destination);
            Console.WriteLine("NQ_V24_NO_NATIVE_NT8_FILLS_NO_FUNDED_EDGE_CERTIFICATE");
            return 0;
        }
        catch(Exception ex)
        {
            Console.Error.WriteLine("NQ_V24_FAIL "+
                ex.GetType().Name+": "+ex.Message);
            return 1;
        }
    }
}
