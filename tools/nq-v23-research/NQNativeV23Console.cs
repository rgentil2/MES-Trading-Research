// Offline .NET 8 host for the *one* complete V23 generator.
// It does not interact with NinjaTrader, place orders or open OOS.
// NinjaTrader historical validation is intentionally a later ONE-TIME
// V25 task after generator/portfolio and V24 throughput are complete.
using System;
using System.IO;
using System.Text;
using System.Text.Json;
using NinjaTrader.NinjaScript.Strategies;
internal static class NQNativeV23Console
{
    static readonly JsonSerializerOptions Json=new JsonSerializerOptions{
        WriteIndented=true,IncludeFields=true,
        PropertyNameCaseInsensitive=false
    };
    static void Help()
    {
        Console.WriteLine("NQ S0.84 V23 -- complete OFFLINE generator/reports");
        Console.WriteLine("  --write-example <jsonPath> : create one search configuration");
        Console.WriteLine("  --run <jsonPath>           : 2020–22 DEV-only GA, audit & reports");
        Console.WriteLine("  --verify <outputDirectory> : SHA256-check complete report package");
        Console.WriteLine("  --version                  : fixed V23 scope");
        Console.WriteLine("No NinjaTrader orders, no 2023+ data loading, no portfolio approval claim.");
    }
    public static int Main(string[] args)
    {
        try
        {
            if(args.Length==1&&args[0]=="--version")
            {
                Console.WriteLine(NQNativeReproducibilityV23.Version);
                return 0;
            }
            if(args.Length!=2){Help();return 2;}
            if(args[0]=="--write-example")
            {
                var example=new NQGeneratorSettingsV23{
                    InputPath="REPLACE_ONLY_WHEN_THE_FINAL_DATASET_IS_READY.txt",
                    OutputDirectory="NQ_V23_RESEARCH_REPORTS",
                    SourceRevision=NQNativeReproducibilityV23.Version
                };
                string file=Path.GetFullPath(args[1]);
                string parent=Path.GetDirectoryName(file);
                if(!Directory.Exists(parent))
                    Directory.CreateDirectory(parent);
                File.WriteAllText(file,
                    JsonSerializer.Serialize(example,Json)+"\n",
                    new UTF8Encoding(false));
                Console.WriteLine("NQ_V23_CONFIG_CREATED "+file);
                return 0;
            }
            if(args[0]=="--verify")
            {
                NQNativeCompleteGeneratorV23.Verify(args[1]);
                Console.WriteLine("NQ_V23_PACKAGE_SHA256_VERIFIED");
                return 0;
            }
            if(args[0]!="--run")
            {Help();return 2;}
            string configPath=Path.GetFullPath(args[1]);
            if(!File.Exists(configPath))
                throw new FileNotFoundException(
                    "V23_CONFIGURATION_NOT_FOUND",configPath);
            var settings=JsonSerializer.Deserialize<NQGeneratorSettingsV23>(
                File.ReadAllText(configPath),Json);
            if(settings==null)
                throw new InvalidDataException("V23_EMPTY_CONFIGURATION");
            string directory=Path.GetDirectoryName(configPath);
            if(!Path.IsPathRooted(settings.InputPath))
                settings.InputPath=Path.GetFullPath(
                    Path.Combine(directory,settings.InputPath));
            if(!Path.IsPathRooted(settings.OutputDirectory))
                settings.OutputDirectory=Path.GetFullPath(
                    Path.Combine(directory,settings.OutputDirectory));
            settings.Validate();
            if(!File.Exists(settings.InputPath))
                throw new FileNotFoundException(
                    "V23_DEVELOPMENT_M1_INPUT_NOT_FOUND",
                    settings.InputPath);
            NQDataLoadV16 dev;
            using(var raw=File.OpenRead(settings.InputPath))
                dev=NQNativeDataLoaderV16.Load(raw,
                    NQDataPartitionV16.Development2020_2022,
                    settings.Instrument,settings.ContractPolicy,
                    settings.MinimumFullSessionsPerMonth);
            var result=NQNativeCompleteGeneratorV23.Run(dev,settings);
            NQNativeCompleteGeneratorV23.Verify(result.OutputDirectory);
            Console.WriteLine("NQ_V23_COMPLETE_RESEARCH_PACKAGE "+
                "reason="+result.Reason+
                " scored="+result.Generated+
                " auditable="+result.Audited+
                " robustPass="+result.IndividualPassed+
                " frozen="+result.FreezeCount+
                " newEconomic="+result.FreshBacktests+
                " reusedEconomic="+result.ReusedBacktests+
                " reportSHA256="+result.PackageSHA256);
            Console.WriteLine("OUTPUT="+result.OutputDirectory);
            Console.WriteLine("NO_REAL_NQ_EDGE_OR_NATIVE_NT8_PARITY_ASSERTED");
            return 0;
        }
        catch(Exception ex)
        {
            Console.Error.WriteLine("NQ_V23_FAIL "+
                ex.GetType().Name+": "+ex.Message);
            return 1;
        }
    }
}
