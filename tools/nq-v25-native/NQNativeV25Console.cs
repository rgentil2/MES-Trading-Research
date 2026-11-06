// V25 ONE final supervised NinjaTrader historical validation campaign.
// --prepare requires an ACTUAL V23 approved 3-5-member frozen portfolio;
// the current synthetic V23 fixture correctly fails that requirement.
// --audit-all consumes NT8 Strategy Analyzer bars/fills in STRICT order:
// DEV 2020-22 -> EXTERNAL 2023-24 -> FINAL 2025-Oct2026.
// No NinjaTrader connection; no order submission; no parameter search.
using System;
using System.IO;
using NinjaTrader.NinjaScript.Strategies;
internal static class NQNativeV25Console
{
    static int Main(string[] args)
    {
        try
        {
            if(args.Length==1&&args[0]=="--version")
            {
                Console.WriteLine(
                    NQNativeV25FrozenSignalCore.Version);
                return 0;
            }
            if(args.Length==3&&args[0]=="--prepare")
            {
                if(File.Exists(args[2]))
                    throw new InvalidOperationException(
                        "V25_ONE_SHOT_HANDOFF_ALREADY_EXISTS");
                var frozen=NQNativeV25FrozenImporter.Load(args[1]);
                NQNativeV25FrozenImporter.WriteHandoff(frozen,args[2]);
                Console.WriteLine("NQ_V25_PREPARE_LOCKED "+
                    "freeze="+frozen.FreezeDigest+
                    " SHA="+frozen.V25LockSHA256+
                    " candidates="+frozen.Candidates.Count);
                Console.WriteLine(
                    "NO_NT8_NATIVE_RUN_OR_MARKET_PROFITABILITY_VERIFIED");
                return 0;
            }
            if(args.Length==5&&args[0]=="--audit-all")
            {
                if(File.Exists(args[4]))
                    throw new InvalidOperationException(
                        "V25_ONE_SHOT_FINAL_REPORT_ALREADY_EXISTS");
                var frozen=NQNativeV25FrozenImporter.Load(args[1]);
                var dev=NQDataPartitionV16.Development2020_2022;
                NQDataLoadV16 original;
                using(var input=File.OpenRead(args[2]))
                    original=NQNativeDataLoaderV16.Load(
                        input,dev,frozen.Instrument,
                        frozen.ContractPolicy,
                        frozen.MinimumFullSessionsPerMonth);
                var verdict=NQNativeV25OneShotValidation.RunAll(
                    frozen,original,args[3]);
                NQNativeV25OneShotValidation.WriteReport(args[4],verdict);
                Console.WriteLine("NQ_V25_FINAL_AUDIT "+
                    verdict.Status+" stages="+verdict.Stages.Count+
                    " candidates="+frozen.Candidates.Count+
                    " lock="+frozen.V25LockSHA256);
                Console.WriteLine("V25_NOT_AUTOMATICALLY_FUNDED_OR_LIVE");
                return verdict.FullPass?0:3;
            }
            Console.WriteLine("V25 fixed objective: ONE final Native NT8 validation.");
            Console.WriteLine("  --prepare <approved V23 folder> <handoff.tsv>");
            Console.WriteLine("  --audit-all <approved V23 folder> "+
                "<original DEV UTC M1 file> <native NT8 report folder> "+
                "<final report.tsv>");
            Console.WriteLine("  --version");
            Console.WriteLine("Inputs MUST be frozen V23 strategies and actual "+
                "native historical 1-minute analyzer fill receipts.");
            Console.WriteLine("No optimization, no interim NT8 validation.");
            return 2;
        }
        catch(Exception ex)
        {
            Console.Error.WriteLine("NQ_V25_FAIL "+
                ex.GetType().Name+": "+ex.Message);
            return 1;
        }
    }
}
