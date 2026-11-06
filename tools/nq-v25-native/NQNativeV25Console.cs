// V25 ONE final supervised NinjaTrader historical validation
// CAMPAIGN, with three irreversible GATES. Not three independent
// optimizations and not background execution:
//  1. --audit-dev checks actual 2020–22 frozen-source vs NT8 fills;
//     ONLY if it passes does it issue DEV approval SHA.
//  2. --audit-external requires DEV SHA, opens 2023–24 once;
//     ONLY if it passes does it issue EXTERNAL approval SHA.
//  3. --audit-final requires both approvals, opens 2025–Oct26 ONCE.
// No live orders or NinjaTrader connection from this console.
using System;
using System.IO;
using NinjaTrader.NinjaScript.Strategies;
internal static class NQNativeV25Console
{
    static void Help()
    {
        Console.WriteLine("V25 fixed objective: ONE final frozen NT8 validation campaign.");
        Console.WriteLine("  --version");
        Console.WriteLine("  --prepare <approved-V23-package> <handoff.tsv>");
        Console.WriteLine("  --audit-dev <approved-V23-package> "+
            "<original-DEV-UTC-M1.txt> <native-NT8-reports> <one-campaign-output>");
        Console.WriteLine("  --audit-external <approved-V23-package> "+
            "<native-NT8-reports> <same-campaign-output>");
        Console.WriteLine("  --audit-final <approved-V23-package> "+
            "<native-NT8-reports> <same-campaign-output>");
        Console.WriteLine("Frozen EXCANv19 genes never change between stages.");
        Console.WriteLine("NT8 must be run in Strategy Analyzer only, never LIVE.");
        Console.WriteLine("NO historical NQ market-profitability or funded-account claim.");
    }
    static string Report(string dir,string scope)
    {return Path.Combine(dir,"V25_"+scope+"_audit.tsv");}
    static int Audit(NQNativeV25FrozenPackage pkg,
        NQNativeV25StageResult stage,string campaignDir,
        string previousApprovalSha)
    {
        Directory.CreateDirectory(campaignDir);
        string report=Report(campaignDir,stage.Scope);
        if(File.Exists(report))
            throw new InvalidOperationException(
                "V25_"+stage.Scope+"_ONCE_ONLY_REPORT_EXISTS");
        NQNativeV25OneShotValidation.WriteStageReport(report,pkg,stage);
        Console.WriteLine("NQ_V25_"+stage.Scope+"_AUDIT "+
            stage.Status+" candidates="+stage.Candidates.Count+
            " bars="+stage.Bars+
            " accountStressDD="+stage.MaxCombinedStressDDUSD);
        if(!stage.Passed)
        {
            Console.WriteLine("V25_FAIL_CLOSED_NO_NEXT_PARTITION");
            return 3;
        }
        if(stage.Scope!="FINAL")
        {
            NQNativeV25StageAuthorization.Approve(
                campaignDir,stage.Scope,pkg.V25LockSHA256,
                report,previousApprovalSha);
            string proof=NQNativeV25StageAuthorization.Verify(
                campaignDir,stage.Scope,pkg.V25LockSHA256,
                previousApprovalSha);
            Console.WriteLine("NQ_V25_"+stage.Scope+
                "_APPROVAL_SHA256="+proof);
            Console.WriteLine("NEXT_NATIVE_SCOPE="+
                (stage.Scope=="DEV"?"EXTERNAL":"FINAL"));
        }
        else
            Console.WriteLine("V25_NATIVE_PARITY_AND_M1_ACCOUNT_RISK_PASS"+
                " (PROVISIONAL; NO LIVE TRADING AUTHORIZATION)");
        return 0;
    }
    public static int Main(string[] args)
    {
        try
        {
            if(args.Length==1&&args[0]=="--version")
            {
                Console.WriteLine(NQNativeV25FrozenSignalCore.Version);
                return 0;
            }
            if(args.Length==3&&args[0]=="--prepare")
            {
                if(File.Exists(args[2]))
                    throw new InvalidOperationException(
                        "V25_ONE_SHOT_HANDOFF_ALREADY_EXISTS");
                var pkg=NQNativeV25FrozenImporter.Load(args[1]);
                NQNativeV25FrozenImporter.WriteHandoff(pkg,args[2]);
                Console.WriteLine("NQ_V25_FROZEN_HANDOFF_READY "+
                    "sha="+pkg.V25LockSHA256+
                    " candidates="+pkg.Candidates.Count+
                    " freeze="+pkg.FreezeDigest);
                Console.WriteLine("NO_NT8_NATIVE_RUN_OR_REAL_EDGE_YET");
                return 0;
            }
            if(args.Length==5&&args[0]=="--audit-dev")
            {
                var pkg=NQNativeV25FrozenImporter.Load(args[1]);
                string campaign=Path.GetFullPath(args[4]);
                if(File.Exists(Report(campaign,"DEV")))
                    throw new InvalidOperationException(
                        "V25_DEV_ONE_SHOT_ALREADY_CONSUMED");
                NQDataLoadV16 development;
                using(var raw=File.OpenRead(args[2]))
                    development=NQNativeDataLoaderV16.Load(raw,
                        NQDataPartitionV16.Development2020_2022,
                        pkg.Instrument,pkg.ContractPolicy,
                        pkg.MinimumFullSessionsPerMonth);
                var stage=NQNativeV25OneShotValidation.AuditDevelopment(
                    pkg,development,args[3]);
                return Audit(pkg,stage,campaign,"");
            }
            if(args.Length==4&&args[0]=="--audit-external")
            {
                var pkg=NQNativeV25FrozenImporter.Load(args[1]);
                string campaign=Path.GetFullPath(args[3]);
                string devProof=NQNativeV25StageAuthorization.Verify(
                    campaign,"DEV",pkg.V25LockSHA256,"");
                if(File.Exists(Report(campaign,"EXTERNAL")))
                    throw new InvalidOperationException(
                        "V25_EXTERNAL_ONE_SHOT_ALREADY_CONSUMED");
                var stage=NQNativeV25OneShotValidation.AuditExternal(
                    pkg,args[2],devProof);
                return Audit(pkg,stage,campaign,devProof);
            }
            if(args.Length==4&&args[0]=="--audit-final")
            {
                var pkg=NQNativeV25FrozenImporter.Load(args[1]);
                string campaign=Path.GetFullPath(args[3]);
                string devProof=NQNativeV25StageAuthorization.Verify(
                    campaign,"DEV",pkg.V25LockSHA256,"");
                string externalProof=NQNativeV25StageAuthorization.Verify(
                    campaign,"EXTERNAL",pkg.V25LockSHA256,devProof);
                if(File.Exists(Report(campaign,"FINAL")))
                    throw new InvalidOperationException(
                        "V25_FINAL_ONE_SHOT_ALREADY_CONSUMED");
                var stage=NQNativeV25OneShotValidation.AuditFinal(
                    pkg,args[2],externalProof);
                return Audit(pkg,stage,campaign,externalProof);
            }
            Help();return 2;
        }
        catch(Exception ex)
        {
            Console.Error.WriteLine("NQ_V25_FAIL "+
                ex.GetType().Name+": "+ex.Message);
            return 1;
        }
    }
}
