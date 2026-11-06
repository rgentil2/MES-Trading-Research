// S0.86 V25: single FINAL, fail-closed native parity campaign.
// DEV (2020-22) is audited first. 2023-24 native OOS data is never
// READ unless DEV passes. 2025-Oct2026 native final is never READ
// unless external passes. Same 3-5 frozen EXCANv19 genes across all.
// No recombination, ranking, GA mutation, parameter fitting, live
// orders or reinterpretation of a synthetic QA fixture as NQ edge.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeV25CandidateResult
    {
        public string Id,Canonical,Scope,ParityStatus;
        public bool Pass;
        public int Trades,MatchedTrades;
        public double ReferenceNetUSD,NativeNetUSD,NativePF,NativeDDUSD;
        public double PriceEntryTickMax,PriceExitTickMax;
    }
    public sealed class NQNativeV25StageResult
    {
        public string Scope,Status;
        public bool Passed;
        public int Bars,Sessions;
        public double MaxCombinedStressDDUSD,MaxDailyLossUSD;
        public readonly List<NQNativeV25CandidateResult> Candidates=
            new List<NQNativeV25CandidateResult>();
    }
    public sealed class NQNativeV25FinalResult
    {
        public string FreezeLock,Status;
        public bool FullPass,DevelopmentPassed,ExternalPassed,FinalPassed;
        public readonly List<NQNativeV25StageResult> Stages=
            new List<NQNativeV25StageResult>();
    }
    public static class NQNativeV25OneShotValidation
    {
        static readonly CultureInfo I=CultureInfo.InvariantCulture;
        static string Nm(double value)
        {return value.ToString("R",I);}
        private static NQHistoricalResultV12 NativeAsHistorical(
            NQHistoricalResultV12 research,
            IList<NQNativeV25NativeTrade> trades,
            IList<NQExecutionFillV12> combined)
        {
            var r=new NQHistoricalResultV12{
                Valid=true,Reason="NATIVE_MANAGED_FILL_MEASUREMENT",
                Score=NQNativeDiscoveryScoreV9.InvalidScore
            };
            for(int i=0;i<trades.Count;i++)
            {
                var x=trades[i];
                // Only called AFTER per-trade parity, with one-to-one
                // matching. Align +/-1m NT8 execution stamp to the
                // completed source bar identified by V12 for M1
                // account stress. This is a proxy, NOT tick sequencing.
                var y=research.Executed[i];
                var fill=new NQExecutionFillV12(
                    y.EntryTime,y.ExitTime,x.Side,x.Quantity,
                    x.EntryPrice,x.ExitPrice,
                    NQNativeV25FrozenSignalCore.ResearchFeeRoundTripUSD);
                r.Executed.Add(fill);combined.Add(fill);
                r.Trades.Add(new NQG0RiskTradeV7(
                    y.EntryTime,y.ExitTime,x.NetUnderResearchFee,0,0));
                r.Net+=x.NetUnderResearchFee;
            }
            return r;
        }
        private static NQNativeV25StageResult AuditStage(
            NQNativeV25FrozenPackage pkg,NQDataPartitionV16 scope,
            string name,string nativeDirectory,
            NQDataLoadV16 originalDev,
            NQNativeV25ParityTolerance tolerances)
        {
            var r=new NQNativeV25StageResult{
                Scope=name,Status="NOT_EVALUATED"
            };
            NQDataLoadV16 source=null;
            var oos=new NQNativeV20OosEvaluator(64L*1024*1024);
            NQNativeSignalCacheV14 devCache=null;
            var fills=new List<NQExecutionFillV12>();
            int first=NQNativeDataLoaderV16.FirstYear(scope),
                last=NQNativeDataLoaderV16.LastYear(scope);
            DateTime from=new DateTime(first,1,1);
            DateTime until=scope==
                NQDataPartitionV16.Development2020_2022?
                    new DateTime(2023,1,1):
                scope==NQDataPartitionV16.ExternalValidation2023_2024?
                    new DateTime(2025,1,1):
                    new DateTime(2026,11,1);
            foreach(var candidate in pkg.Candidates)
            {
                string prefix=Path.Combine(nativeDirectory,
                    "V25_"+candidate.Id+"_"+name);
                var bars=NQNativeV25NativeBarsReader.Load(
                    prefix+"_bars.tsv",pkg.V25LockSHA256,scope,
                    pkg.Instrument,pkg.ContractPolicy,
                    pkg.MinimumFullSessionsPerMonth);
                if(source==null)
                {
                    source=bars;
                    if(scope==NQDataPartitionV16.Development2020_2022)
                    {
                        if(originalDev==null||originalDev.Bars==null||
                           NQNativeReproducibilityV23.SourceBarsHash(
                               originalDev)!=pkg.SourceBarsSHA256)
                            throw new InvalidDataException(
                                "V25_SOURCE_DIFFERS_FROM_FROZEN_DEV");
                        NQNativeV25NativeBarsReader.RequireBarByBarEquality(
                            originalDev.Bars,source.Bars);
                        devCache=new NQNativeSignalCacheV14(
                            source.Bars,64L*1024*1024,64L*1024*1024,
                            NQNativeConditionCatalogV19.Count,
                            (bars,type,period)=>
                            {
                                bool b,s;
                                if(!NQNativeConditionCatalogV19.TryEvaluate(
                                    bars,type,period,out b,out s)||
                                   b&&s)return -2;
                                return b?1:s?-1:0;
                            });
                    }
                    r.Bars=source.Bars.Count;
                    r.Sessions=source.Manifest.CompleteRthDays;
                }
                else
                    NQNativeV25NativeBarsReader.RequireBarByBarEquality(
                        source.Bars,bars.Bars);
                var reference=scope==
                    NQDataPartitionV16.Development2020_2022?
                    devCache.EvaluateExpanded(candidate.Genes,
                        NQNativeExitCanonicalV19.Analyze):
                    oos.Evaluate(source.Bars,candidate.Genes,first,last);
                var native=NQNativeV25ParityAudit.LoadNativeTsv(
                    prefix+"_native_trades.tsv",
                    candidate.CanonicalId,pkg.V25LockSHA256);
                var parity=NQNativeV25ParityAudit.Compare(
                    reference,native,tolerances);
                // The native account risk has no valid meaning when
                // the native fills do not match a complete V12 pairing.
                // Fail closed on the FIRST member mismatch.
                if(!parity.ProvisionalPass)
                {
                    r.Candidates.Add(new NQNativeV25CandidateResult{
                        Id=candidate.Id,Canonical=candidate.CanonicalId,
                        Scope=name,ParityStatus=parity.Status,Pass=false,
                        Trades=native.Count,MatchedTrades=parity.Matched,
                        ReferenceNetUSD=parity.ResearchNetUSD,
                        NativeNetUSD=parity.NativeModelNetUSD
                    });
                    r.Status="V25_NATIVE_FILL_PARITY_REJECT";
                    return r;
                }
                var asNative=NativeAsHistorical(reference,native,fills);
                var metric=NQNativeFoldScoreV15.Score(asNative,from,until);
                bool accepted=metric.Valid&&metric.PeriodGatePass &&
                    native.Count>=5*metric.Months;
                r.Candidates.Add(new NQNativeV25CandidateResult{
                    Id=candidate.Id,Canonical=candidate.CanonicalId,
                    Scope=name,ParityStatus=parity.Status,Pass=accepted,
                    Trades=native.Count,MatchedTrades=parity.Matched,
                    ReferenceNetUSD=parity.ResearchNetUSD,
                    NativeNetUSD=parity.NativeModelNetUSD,
                    NativePF=metric.ProfitFactor,
                    NativeDDUSD=metric.ClosedDDUSD,
                    PriceEntryTickMax=parity.MaximumEntryTickDelta,
                    PriceExitTickMax=parity.MaximumExitTickDelta
                });
                if(!accepted)
                {
                    r.Status="V25_NATIVE_MONTHLY_PF_NET_OR_DD_REJECT";
                    return r;
                }
            }
            var account=scope==
                NQDataPartitionV16.Development2020_2022?
                NQNativeChronologicalRiskV15.Evaluate(
                    source.Bars,fills,pkg.AccountRisk):
                NQNativeChronologicalRiskV15.EvaluateHeldout(
                    source.Bars,fills,pkg.AccountRisk,first,last);
            r.MaxCombinedStressDDUSD=account.MaxAdversarialM1StressDDUSD;
            r.MaxDailyLossUSD=account.MaxSessionPeakToTroughUSD;
            r.Passed=account.Valid&&account.ProvisionalPass&&
                r.Candidates.Count==pkg.Candidates.Count&&
                r.Candidates.All(x=>x.Pass);
            r.Status=r.Passed?
                "V25_"+name+"_PROVISIONAL_NATIVE_PARITY_PASS":
                "V25_COMBINED_ACCOUNT_M1_RISK_REJECT";
            return r;
        }

        // One final audit consumes already-created Native Analyzer
        // receipts, reading DEV first; no OOS file is read if a prior
        // gate rejects. The 3 scopes are one planned final campaign
        // with immutable genes and report SHA, NOT three optimizations.
        public static NQNativeV25FinalResult RunAll(
            NQNativeV25FrozenPackage pkg,
            NQDataLoadV16 originalDevelopment,
            string nativeReportsDirectory,
            NQNativeV25ParityTolerance tolerances=null)
        {
            if(pkg==null||pkg.Candidates.Count<3||
               pkg.Candidates.Count>5||
               String.IsNullOrWhiteSpace(nativeReportsDirectory))
                throw new ArgumentException(
                    "V25_REQUIRES_ACTUAL_3_TO_5_FROZEN_AND_NATIVE_RECEIPTS");
            tolerances=tolerances??new NQNativeV25ParityTolerance();
            var r=new NQNativeV25FinalResult{
                FreezeLock=pkg.V25LockSHA256,
                Status="FINAL_NEVER_EVALUATED"
            };
            var dev=AuditStage(pkg,
                NQDataPartitionV16.Development2020_2022,
                "DEV",nativeReportsDirectory,originalDevelopment,tolerances);
            r.Stages.Add(dev);
            r.DevelopmentPassed=dev.Passed;
            if(!dev.Passed)
            {r.Status="V25_DEV_NATIVE_GATE_REJECT_FINAL_UNOPENED";return r;}
            var ext=AuditStage(pkg,
                NQDataPartitionV16.ExternalValidation2023_2024,
                "EXTERNAL",nativeReportsDirectory,null,tolerances);
            r.Stages.Add(ext);r.ExternalPassed=ext.Passed;
            if(!ext.Passed)
            {r.Status="V25_EXTERNAL_GATE_REJECT_FINAL_UNOPENED";return r;}
            var final=AuditStage(pkg,
                NQDataPartitionV16.FinalHoldout2025_2026,
                "FINAL",nativeReportsDirectory,null,tolerances);
            r.Stages.Add(final);r.FinalPassed=final.Passed;
            r.FullPass=dev.Passed&&ext.Passed&&final.Passed;
            r.Status=r.FullPass?
                "V25_THREE_PARTITIONS_NATIVE_PARITY_PROVISIONALLY_PASS":
                "V25_FINAL_NATIVE_PARITY_OR_ACCOUNT_RISK_REJECT";
            return r;
        }
        public static void WriteReport(string path,
            NQNativeV25FinalResult report)
        {
            if(report==null||String.IsNullOrWhiteSpace(path))
                throw new ArgumentNullException("V25_REPORT");
            using(var w=new StreamWriter(path,false,new UTF8Encoding(false)))
            {
                w.WriteLine("freezeSHA256\t"+report.FreezeLock);
                w.WriteLine("status\t"+report.Status);
                w.WriteLine("nativeFullPass\t"+(report.FullPass?"1":"0"));
                w.WriteLine("scope\tstatus\tbars\tsessions\t"+
                    "combinedStressDDUSD\tmaxSessionLossUSD");
                foreach(var x in report.Stages)
                {
                    w.WriteLine(String.Join("\t",new[]{
                        x.Scope,x.Status,x.Bars.ToString(I),
                        x.Sessions.ToString(I),
                        Nm(x.MaxCombinedStressDDUSD),Nm(x.MaxDailyLossUSD)
                    }));
                    w.WriteLine("candidateId\tcanonicalBase64"+
                        "\ttrades\tmatched\tresearchNetUSD"+
                        "\tnativeNetUSD\tnativePF\tnativeDDUSD"+
                        "\tmaxEntryTickDelta\tmaxExitTickDelta\tstatus");
                    foreach(var m in x.Candidates)
                        w.WriteLine(String.Join("\t",new[]{
                            m.Id,Convert.ToBase64String(Encoding.UTF8.GetBytes(
                                m.Canonical)),m.Trades.ToString(I),
                            m.MatchedTrades.ToString(I),
                            Nm(m.ReferenceNetUSD),Nm(m.NativeNetUSD),
                            Nm(m.NativePF),Nm(m.NativeDDUSD),
                            Nm(m.PriceEntryTickMax),Nm(m.PriceExitTickMax),
                            m.ParityStatus+"|"+(m.Pass?"PASS":"REJECT")
                        }));
                }
                w.WriteLine("IMPORTANT\tPROVISIONAL_M1_RESEARCH_ONLY");
                w.WriteLine("NOT_CLAIMED\tLIVE_TRADING_OR_FUNDED_ACCOUNT_APPROVAL");
            }
        }
    }
}
