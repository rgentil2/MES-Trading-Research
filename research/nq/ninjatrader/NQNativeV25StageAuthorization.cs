// S0.86 V25: staged authorization for ONE final validation campaign.
// Actual NT8 Analyzer historical DEV must pass before EXTERNAL runs;
// EXTERNAL must pass before FINAL is permitted. Durable SHA chain
// discourages accidental reuse/changes. NOT a third-party signature.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public static class NQNativeV25StageAuthorization
    {
        private static string Key(string name,string value)
        {return name+"\t"+value;}
        public static string ApprovalPath(string directory,string scope)
        {
            if(scope!="DEV"&&scope!="EXTERNAL")
                throw new ArgumentException("ONLY_PRIOR_V25_GATES_AUTHORIZE");
            return Path.Combine(directory,"V25_"+scope+"_PASSED.sha256");
        }
        public static void Approve(string directory,string scope,
            string freezeLock,string stageReport,
            string previousApprovalSHA256)
        {
            if(String.IsNullOrWhiteSpace(directory)||
               String.IsNullOrWhiteSpace(stageReport)||
               freezeLock==null||freezeLock.Length!=64||
               previousApprovalSHA256==null||
               previousApprovalSHA256.Length!=0&&
               previousApprovalSHA256.Length!=64||
               scope=="DEV"&&previousApprovalSHA256.Length!=0||
               scope=="EXTERNAL"&&previousApprovalSHA256.Length!=64)
                throw new ArgumentException("V25_BAD_GATE_SHA_CHAIN");
            string path=ApprovalPath(directory,scope);
            if(File.Exists(path))
                throw new InvalidOperationException(
                    "V25_ONCE_ONLY_PRIOR_GATE_ALREADY_APPROVED");
            using(var w=new StreamWriter(new FileStream(
                path,FileMode.CreateNew,FileAccess.Write,FileShare.None),
                new UTF8Encoding(false)))
            {
                w.WriteLine(Key("version",
                    NQNativeV25FrozenSignalCore.Version));
                w.WriteLine(Key("scope",scope));
                w.WriteLine(Key("V25LockSHA256",freezeLock));
                w.WriteLine(Key("reportSHA256",
                    NQNativeReproducibilityV23.SHAFile(stageReport)));
                w.WriteLine(Key("previousGateSHA256",
                    previousApprovalSHA256));
                w.WriteLine(Key("verdict","PROVISIONAL_PASS"));
            }
        }
        public static string Verify(string directory,string scope,
            string freezeLock,string previousApprovalSHA256)
        {
            string path=ApprovalPath(directory,scope);
            string report=Path.Combine(directory,
                "V25_"+scope+"_audit.tsv");
            if(!File.Exists(path)||!File.Exists(report))
                throw new InvalidOperationException(
                    "V25_"+scope+"_PREVIOUS_GATE_NOT_AUTHORIZED");
            string[] lines=File.ReadAllLines(path);
            string[] expected={
                Key("version",NQNativeV25FrozenSignalCore.Version),
                Key("scope",scope),
                Key("V25LockSHA256",freezeLock),
                Key("reportSHA256",
                    NQNativeReproducibilityV23.SHAFile(report)),
                Key("previousGateSHA256",previousApprovalSHA256),
                Key("verdict","PROVISIONAL_PASS")
            };
            if(!lines.SequenceEqual(expected,StringComparer.Ordinal))
                throw new InvalidDataException(
                    "V25_GATE_LOCK_OR_REPORT_CHANGED");
            return NQNativeReproducibilityV23.SHAFile(path);
        }
    }
}
