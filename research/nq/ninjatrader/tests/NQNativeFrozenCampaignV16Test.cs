// V16 frozen external/final evaluation on NT8-format SYNTHETIC text.
// Development approval is a synthetic stub here; actual source-gates
// were exercised in the V13/V15 integration tests. NO real NQ returns.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using NinjaTrader.NinjaScript.Strategies;

internal static class V16FrozenCampaignTest
{
    static void A(bool yes,string msg)
    {if(!yes)throw new Exception("NQ_V16_CAMPAIGN_FAIL "+msg);}
    static TimeZoneInfo Eastern()
    {
        foreach(string id in new[]{"Eastern Standard Time","America/New_York"})
            try{return TimeZoneInfo.FindSystemTimeZoneById(id);}
            catch(TimeZoneNotFoundException){}
        throw new Exception("Missing US Eastern");
    }
    static string Feed(int firstYear,int finalYear,
                       int finalMonth=12,bool flat=false)
    {
        var z=Eastern();var s=new StringBuilder();
        int[] days={1,5,9,13,17,21,25,28};
        for(int y=firstYear;y<=finalYear;y++)
            for(int month=1;month<=12;month++)
            {
                if(y==finalYear&&month>finalMonth)break;
                foreach(int day in days)
                {
                    var date=new DateTime(y,month,day);
                    for(int min=0;min<210;min++)
                    {
                        DateTime et=DateTime.SpecifyKind(
                            date.AddHours(8).AddMinutes(min),
                            DateTimeKind.Unspecified);
                        DateTime utc=TimeZoneInfo.ConvertTimeToUtc(
                            et.AddMinutes(1),z);
                        decimal price=15000m+(flat?0m:min*0.75m);
                        s.Append(utc.ToString("yyyyMMdd HHmmss",
                          CultureInfo.InvariantCulture)).Append(';')
                         .Append(price.ToString(CultureInfo.InvariantCulture))
                         .Append(';')
                         .Append((price+0.25m).ToString(CultureInfo.InvariantCulture))
                         .Append(';')
                         .Append((price-0.25m).ToString(CultureInfo.InvariantCulture))
                         .Append(';')
                         .Append(price.ToString(CultureInfo.InvariantCulture))
                         .Append(";250\n");
                    }
                }
            }
        return s.ToString();
    }
    static NQDataLoadV16 Load(string txt,NQDataPartitionV16 p,
                             string policy="BACKADJUSTED_UNVERIFIED")
    {
        using(var m=new MemoryStream(Encoding.UTF8.GetBytes(txt)))
            return NQNativeDataLoaderV16.Load(m,p,"NQ CONTINUOUS",policy,0);
    }
    static int[] Genes(int period)
    {
        return new[]{1,0,period,44,12,77,12,121,12,
            0,0,0,0,20,32,2,0,14,15,25};
    }
    static NQNativeFrozenCampaignV16 Campaign(DateTime cutoff)
    {
        // Minimal fixture proof of gate dependency, NOT evidence of a
        // genuine V13 portfolio selection on historical NQ.
        var selection=new NQPortfolioResultV13{Valid=true,
            Reason="SYNTHETIC_PROOF"};
        selection.Selected.Add(new NQPortfolioCandidateV13(
            "A",new List<NQG0RiskTradeV7>()));
        selection.Selected.Add(new NQPortfolioCandidateV13(
            "B",new List<NQG0RiskTradeV7>()));
        selection.Selected.Add(new NQPortfolioCandidateV13(
            "C",new List<NQG0RiskTradeV7>()));
        var proof=new NQIntegratedPortfolioRiskResultV15{
            Valid=true,ProvisionalPass=true,Selection=selection,
            Chronology=new NQChronologicalRiskResultV15{
                Valid=true,ProvisionalPass=true
            }
        };
        var dev=new NQDataManifestV16(
            NQDataPartitionV16.Development2020_2022,
            "NQ CONTINUOUS","BACKADJUSTED_UNVERIFIED",
            new string('a',64),
            new DateTime(2020,1,1),new DateTime(2022,12,31),
            new DateTime(2020,1,1),new DateTime(2022,12,31),
            200000,200000,540,Enumerable.Repeat(15,36).ToArray());
        return new NQNativeFrozenCampaignV16(dev,proof,
            new[]{
                new NQFrozenCandidateV16("A",Genes(6)),
                new NQFrozenCandidateV16("B",Genes(12)),
                new NQFrozenCandidateV16("C",Genes(18))
            },
            new NQChronologicalRiskConfigV15{
                MaxAccountStressDDUSD=2000,
                MaxSessionPeakToTroughUSD=1000,
                MaxConcurrentAdverseUSD=1000
            },8,cutoff);
    }
    static void Locked(Action action,string reason)
    {
        try{action();throw new Exception("UNEXPECTEDLY_PERMITTED_"+reason);}
        catch(InvalidOperationException e)
        {A(e.Message.Contains(reason),
            "expected lock "+reason+" got "+e.Message);}
    }
    public static int Main()
    {
        var external=Load(Feed(2023,2024),
            NQDataPartitionV16.ExternalValidation2023_2024);
        var final=Load(Feed(2025,2026,10),
            NQDataPartitionV16.FinalHoldout2025_2026);
        A(external.Manifest.FullSessionsByMonth.Length==24 &&
          external.Manifest.FullSessionsByMonth.All(x=>x==8),
          "full 2023–24 external coverage");
        A(final.Manifest.FullSessionsByMonth.Length==24 &&
          final.Manifest.FullSessionsByMonth.Take(22).All(x=>x==8) &&
          final.Manifest.FullSessionsByMonth.Skip(22).All(x=>x==0),
          "2025 Jan–Oct 2026 final snapshot; no future Nov/Dec data");
        var cutoff=new DateTime(2026,11,1);
        var campaign=Campaign(cutoff);
        A(campaign.FreezeDigest.Length==64,"frozen SHA256 identity");
        Locked(()=>campaign.EvaluateFinal(final),
            "FINAL_LOCKED_PENDING_EXTERNAL_PASS");
        var ext=campaign.EvaluateExternal(external);
        A(ext.Valid&&ext.ProvisionalPass&&
          ext.Candidates.Count==3&&
          ext.Candidates.All(x=>x.Economic.Valid&&
            x.Economic.PeriodGatePass&&x.Fills>0),
          "all three frozen external candidates pass synthetic economics");
        A(ext.AccountRisk.Valid&&ext.AccountRisk.ProvisionalPass&&
          ext.AccountRisk.FillCount>0,
          "combined external minute risk checked");
        A(campaign.ExternalAccepted,"external gate unlocks final only after pass");
        Locked(()=>campaign.EvaluateExternal(external),
            "EXTERNAL_REEVALUATION_FORBIDDEN");

        var res=campaign.EvaluateFinal(final);
        A(res.Valid&&res.ProvisionalPass&&res.Candidates.Count==3,
          "one-shot frozen Jan2025-Oct2026 holdout measured");
        A(res.EndExclusive==cutoff&&campaign.FinalConsumed,
          "final cutoff preserved and holdout consumed");
        A(res.FreezeDigest==ext.FreezeDigest,
          "exact same prior frozen genomes, no retune");
        A(res.ExportSha256!=ext.ExportSha256,
          "external and final distinct datasets");
        A(res.Candidates.Zip(ext.Candidates,(a,b)=>
            a.Id==b.Id&&a.CanonicalId==b.CanonicalId).All(x=>x),
          "same three exact canonical genomes across both OOS periods");
        Locked(()=>campaign.EvaluateFinal(final),
            "FINAL_HOLDOUT_REUSE_FORBIDDEN");

        var noEdge=Campaign(cutoff);
        var flatExternal=Load(Feed(2023,2024,12,true),
            NQDataPartitionV16.ExternalValidation2023_2024);
        var rejected=noEdge.EvaluateExternal(flatExternal);
        A(rejected.Valid&&!rejected.ProvisionalPass&&
          !noEdge.ExternalAccepted,"flat OOS fails frequency/fitness");
        Locked(()=>noEdge.EvaluateFinal(final),
            "FINAL_LOCKED_PENDING_EXTERNAL_PASS");

        var provenance=Campaign(cutoff);
        var altered=Load(Feed(2023,2024),
            NQDataPartitionV16.ExternalValidation2023_2024,
            "DO_NOT_MERGE");
        Locked(()=>provenance.EvaluateExternal(altered),
            "DATASET_PROVENANCE_OR_PARTITION_MISMATCH");

        var wrongPartition=Campaign(cutoff);
        Locked(()=>wrongPartition.EvaluateExternal(final),
            "DATASET_PROVENANCE_OR_PARTITION_MISMATCH");

        var earlyCutoff=Campaign(new DateTime(2026,7,1));
        // Cannot reveal bars past the declared final cutoff even if the
        // future file is given. Need external acceptance first.
        earlyCutoff.EvaluateExternal(external);
        Locked(()=>earlyCutoff.EvaluateFinal(final),
            "DATA_AFTER_FROZEN_CUTOFF");

        Console.WriteLine("NQ_V16_FROZEN_CAMPAIGN_PASS "+
            "externalFills="+ext.AccountRisk.FillCount+
            " finalFills="+res.AccountRisk.FillCount+
            " frozenCandidates="+res.Candidates.Count+
            " finalCutoff="+res.EndExclusive.ToString("yyyy-MM-dd")+
            " digest="+res.FreezeDigest.Substring(0,16)+
            " noRefit=TRUE noReuse=TRUE");
        Console.WriteLine("SYNTHETIC_ECONOMICS_AND_DEVELOPMENT_PROOF_ONLY_NO_REAL_NQ");
        return 0;
    }
}
