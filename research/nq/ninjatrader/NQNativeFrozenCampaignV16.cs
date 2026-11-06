// S0.76 — frozen, single-pass OOS validation campaign.
// Development candidate IDs/genomes/contract policy are frozen BEFORE
// opening 2023–24 validation. 2025–26 final holdout is accessible only
// after ALL preselected candidates and combined M1 account chronology
// pass the external validation gate. NO genetic search or mutation here.
// One-shot guards are per in-memory campaign, NOT cryptographic prevention
// of creating an entirely new campaign or inspecting final results.
// Source is a read-only NinjaTrader UTC end-of-minute export adapter.
// Research only; the final proprietary NinjaTrader replay is STILL needed.
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQFrozenCandidateV16
    {
        public readonly string Id,CanonicalId;
        private readonly int[] genes;
        public NQFrozenCandidateV16(string id,int[] genome)
            : this(id,genome,NQNativeExitCanonicalV11.Analyze)
        {}

        // V20 freezes genuine EXCANv19 identities. Older V16 callers
        // retain V11 semantics; never coerce new signals into old IDs.
        public NQFrozenCandidateV16(string id,int[] genome,
            Func<int[],NQExitIdentityV11> canonicalizer)
        {
            if(String.IsNullOrWhiteSpace(id)||genome==null||
               genome.Length!=20||canonicalizer==null)
                throw new ArgumentException("Frozen candidate id/20 genes/canonicalizer required");
            var c=canonicalizer(genome);
            if(c.IsRedundant)
                throw new ArgumentException("Redundant candidate not freezeable");
            Id=id;CanonicalId=c.RuntimeKey;
            genes=(int[])genome.Clone();
        }
        public int[] Genes{get{return (int[])genes.Clone();}}
    }

    public sealed class NQHoldoutMetricsV16
    {
        public readonly string Id,CanonicalId;
        public readonly NQFoldMetricsV15 Economic;
        public readonly int Fills;
        public NQHoldoutMetricsV16(string id,string canonicalId,
            NQFoldMetricsV15 economic,int fills)
        {Id=id;CanonicalId=canonicalId;Economic=economic;Fills=fills;}
    }

    public sealed class NQHoldoutCampaignResultV16
    {
        public NQDataPartitionV16 Partition;
        public string FreezeDigest,ExportSha256,Reason;
        public readonly List<NQHoldoutMetricsV16> Candidates=
            new List<NQHoldoutMetricsV16>();
        public NQChronologicalRiskResultV15 AccountRisk;
        public bool Valid,ProvisionalPass;
        public DateTime EndExclusive;
    }

    public sealed class NQNativeFrozenCampaignV16
    {
        private readonly NQDataManifestV16 development;
        private readonly ReadOnlyCollection<NQFrozenCandidateV16> chosen;
        private readonly int minimumCompleteDaysPerMonth;
        private readonly NQChronologicalRiskConfigV15 risk;
        private readonly DateTime finalCutoffExclusive;
        private readonly string freezeDigest;
        private readonly Func<IList<NQTimedBarV12>,int[],int,int,
            NQHistoricalResultV12> versionedOosEvaluator;
        private readonly string evaluatorVersion;
        private bool externalConsumed,externalAccepted,finalConsumed;

        public string FreezeDigest{get{return freezeDigest;}}
        public bool ExternalAccepted{get{return externalAccepted;}}
        public bool FinalConsumed{get{return finalConsumed;}}

        public NQNativeFrozenCampaignV16(NQDataManifestV16 developmentManifest,
            NQIntegratedPortfolioRiskResultV15 developmentRisk,
            IList<NQFrozenCandidateV16> frozen,
            NQChronologicalRiskConfigV15 riskConfig,
            int minimumDaysPerMonth,DateTime finalEndExclusive)
            : this(developmentManifest,developmentRisk,frozen,riskConfig,
                minimumDaysPerMonth,finalEndExclusive,null,null)
        {}

        // Versioned V19 evaluator is only for an already-frozen OOS
        // candidate portfolio; no generator or training rank is passed
        // to this stage. Frozen digest binds V20 scorer implementation.
        public NQNativeFrozenCampaignV16(NQDataManifestV16 developmentManifest,
            NQIntegratedPortfolioRiskResultV15 developmentRisk,
            IList<NQFrozenCandidateV16> frozen,
            NQChronologicalRiskConfigV15 riskConfig,
            int minimumDaysPerMonth,DateTime finalEndExclusive,
            Func<IList<NQTimedBarV12>,int[],int,int,
                NQHistoricalResultV12> externalEvaluator,
            string externalEvaluatorVersion)
        {
            if((externalEvaluator==null)!=(externalEvaluatorVersion==null)||
               externalEvaluatorVersion!=null&&
                   String.IsNullOrWhiteSpace(externalEvaluatorVersion))
                throw new ArgumentException("Versioned evaluator and ID required together");
            versionedOosEvaluator=externalEvaluator;
            evaluatorVersion=externalEvaluatorVersion;
            if(developmentManifest==null ||
               developmentManifest.Partition!=
                    NQDataPartitionV16.Development2020_2022 ||
               String.IsNullOrEmpty(developmentManifest.Sha256) ||
               developmentRisk==null||!developmentRisk.Valid||
               !developmentRisk.ProvisionalPass||
               developmentRisk.Selection==null||
               !developmentRisk.Selection.Valid||
               developmentRisk.Chronology==null||
               !developmentRisk.Chronology.ProvisionalPass ||
               frozen==null||frozen.Count<3||frozen.Count>5||
               riskConfig==null ||minimumDaysPerMonth<1 ||
               finalEndExclusive.Year<2025 ||
               finalEndExclusive.Year>2027 ||
               finalEndExclusive.Month<1 ||
               finalEndExclusive.Day!=1 ||
               finalEndExclusive.TimeOfDay!=TimeSpan.Zero ||
               finalEndExclusive<=new DateTime(2025,1,1) ||
               finalEndExclusive>new DateTime(2027,1,1))
                throw new ArgumentException(
                    "Need 3–5 development-approved frozen genes, risk and valid OOS cutoff");
            riskConfig.Validate();
            if(developmentManifest.FullSessionsByMonth==null||
               developmentManifest.FullSessionsByMonth.Length!=36 ||
               developmentManifest.FullSessionsByMonth.Any(x=>
                   x<minimumDaysPerMonth))
                throw new ArgumentException("Incomplete development manifest");
            var expected=new HashSet<string>(
                developmentRisk.Selection.Selected.Select(x=>x.Id),
                StringComparer.Ordinal);
            var ids=new HashSet<string>(StringComparer.Ordinal);
            var keys=new HashSet<string>(StringComparer.Ordinal);
            foreach(var f in frozen)
            {
                if(f==null||!expected.Contains(f.Id)||
                   !ids.Add(f.Id)||!keys.Add(f.CanonicalId))
                    throw new ArgumentException(
                        "Unapproved/duplicate candidate or canonical genome");
            }
            if(expected.Count!=frozen.Count)
                throw new ArgumentException("Frozen candidates must exactly match V13");
            development=developmentManifest;
            chosen=new List<NQFrozenCandidateV16>(
                frozen.OrderBy(x=>x.Id,StringComparer.Ordinal)).AsReadOnly();
            minimumCompleteDaysPerMonth=minimumDaysPerMonth;
            finalCutoffExclusive=finalEndExclusive;
            risk=riskConfig;
            using(var sha=SHA256.Create())
            {
                string body=development.Sha256+"\n"+
                    development.Instrument+"\n"+
                    development.ContractPolicy+"\n"+
                    finalEndExclusive.ToString("yyyy-MM-dd")+"\n"+
                    String.Join("\n",chosen.Select(x=>
                        x.Id+"|"+x.CanonicalId))+
                    (evaluatorVersion==null?"":"\nOOS_EVALUATOR_VERSION="+
                        evaluatorVersion);
                freezeDigest=BitConverter.ToString(
                    sha.ComputeHash(Encoding.UTF8.GetBytes(body)))
                    .Replace("-","").ToLowerInvariant();
            }
        }

        private void ValidatePartition(NQDataLoadV16 supplied,
            NQDataPartitionV16 partition,DateTime endExclusive)
        {
            if(supplied==null||supplied.Manifest==null||
               supplied.Bars==null||supplied.Bars.Count==0||
               supplied.Manifest.Partition!=partition||
               supplied.Manifest.Instrument!=development.Instrument||
               supplied.Manifest.ContractPolicy!=development.ContractPolicy||
               supplied.Manifest.Sha256==development.Sha256||
               String.IsNullOrWhiteSpace(supplied.Manifest.Sha256))
                throw new InvalidOperationException("DATASET_PROVENANCE_OR_PARTITION_MISMATCH");
            DateTime begin=new DateTime(
                NQNativeDataLoaderV16.FirstYear(partition),1,1);
            int months=(endExclusive.Year-begin.Year)*12+
                endExclusive.Month-begin.Month;
            if(months<1||supplied.Manifest.FullSessionsByMonth.Length<
               months)
                throw new InvalidOperationException("INCOMPLETE_FROZEN_OOS_MONTHS");
            for(int i=0;i<months;i++)
                if(supplied.Manifest.FullSessionsByMonth[i]<
                   minimumCompleteDaysPerMonth)
                    throw new InvalidOperationException(
                        "INCOMPLETE_FROZEN_OOS_MONTHS");
            foreach(var t in supplied.Bars)
                if(t.Time<begin||t.Time>=endExclusive)
                    throw new InvalidOperationException("DATA_AFTER_FROZEN_CUTOFF");
        }

        private NQHoldoutCampaignResultV16 RunSegment(
            NQDataLoadV16 dataset,NQDataPartitionV16 partition,
            DateTime until)
        {
            var response=new NQHoldoutCampaignResultV16{
                Partition=partition,FreezeDigest=freezeDigest,
                ExportSha256=dataset.Manifest.Sha256,
                EndExclusive=until,Valid=true,
                Reason="FROZEN_OOS_MEASUREMENT_ONLY"
            };
            DateTime from=new DateTime(
                NQNativeDataLoaderV16.FirstYear(partition),1,1);
            var all=new List<NQExecutionFillV12>();
            bool eachPass=true;
            foreach(var candidate in chosen)
            {
                int[] genes=candidate.Genes;
                var replay=versionedOosEvaluator==null?
                    NQNativeHistoricalEvaluatorV12.EvaluateHeldout(
                        dataset.Bars,genes,
                        NQNativeDataLoaderV16.FirstYear(partition),
                        NQNativeDataLoaderV16.LastYear(partition)):
                    versionedOosEvaluator(dataset.Bars,genes,
                        NQNativeDataLoaderV16.FirstYear(partition),
                        NQNativeDataLoaderV16.LastYear(partition));
                var economics=NQNativeFoldScoreV15.Score(replay,from,until);
                response.Candidates.Add(new NQHoldoutMetricsV16(
                    candidate.Id,candidate.CanonicalId,economics,
                    replay.Executed.Count));
                if(!replay.Valid||!economics.Valid||
                   !economics.PeriodGatePass)
                    eachPass=false;
                all.AddRange(replay.Executed);
            }
            response.AccountRisk=NQNativeChronologicalRiskV15.EvaluateHeldout(
                dataset.Bars,all,risk,
                    NQNativeDataLoaderV16.FirstYear(partition),
                    NQNativeDataLoaderV16.LastYear(partition));
            if(!response.AccountRisk.Valid)
            {
                response.Valid=false;
                response.Reason="INVALID_FROZEN_M1_ACCOUNT_CHRONOLOGY";
                return response;
            }
            response.ProvisionalPass=eachPass&&
                response.AccountRisk.ProvisionalPass;
            if(!response.ProvisionalPass)
                response.Reason="FROZEN_ECONOMICS_OR_ACCOUNT_RISK_REJECT";
            return response;
        }

        public NQHoldoutCampaignResultV16 EvaluateExternal(
            NQDataLoadV16 dataset)
        {
            if(externalConsumed)
                throw new InvalidOperationException("EXTERNAL_REEVALUATION_FORBIDDEN");
            ValidatePartition(dataset,
                NQDataPartitionV16.ExternalValidation2023_2024,
                new DateTime(2025,1,1));
            externalConsumed=true; // never accidentally tune then repeat
            var scored=RunSegment(dataset,
                NQDataPartitionV16.ExternalValidation2023_2024,
                new DateTime(2025,1,1));
            externalAccepted=scored.Valid&&scored.ProvisionalPass;
            return scored;
        }

        public NQHoldoutCampaignResultV16 EvaluateFinal(
            NQDataLoadV16 dataset)
        {
            if(!externalConsumed||!externalAccepted)
                throw new InvalidOperationException(
                    "FINAL_LOCKED_PENDING_EXTERNAL_PASS");
            if(finalConsumed)
                throw new InvalidOperationException("FINAL_HOLDOUT_REUSE_FORBIDDEN");
            ValidatePartition(dataset,
                NQDataPartitionV16.FinalHoldout2025_2026,
                finalCutoffExclusive);
            finalConsumed=true;
            return RunSegment(dataset,
                NQDataPartitionV16.FinalHoldout2025_2026,
                finalCutoffExclusive);
        }
    }
}
