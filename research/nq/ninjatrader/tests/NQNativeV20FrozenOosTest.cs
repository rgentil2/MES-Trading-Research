// V20 frozen EXCANv19 external 2023–24 read-only validation with
// original V12 conservative fills and V15 combined mark-to-market risk.
// 3-candidate DEV "approved" stub is ONLY a fixture for frozen-gate
// isolation; it never proves three real profitable NQ strategies.
// Enforces external single-pass, blocked final on failure, immutable
// EXCANv19 identity and versioned OOS evaluator checksum binding.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V20FrozenExternalTest
{
    private static void A(bool yes,string why)
    {if(!yes)throw new Exception("NQ_V20_FROZEN_FAIL "+why);}
    private static int[] Genes(int family,int period)
    {
        return new[]{1,family*11,period,789,12,999,12,1319,12,
            0,0,0,0,20,32,2,0,14,15,25};
    }
    private static NQDataLoadV16 Source(int first,int last,
                                        bool altered=false,
                                        bool smoothUptrend=false,
                                        int finalMonth=12)
    {
        var bars=new List<NQTimedBarV12>(27000);
        var days=new[]{1,5,9,13,17,21,25,28};
        var monthly=new int[(last-first+1)*12];
        double price=15000;
        for(int y=first;y<=last;y++)
          for(int m=1;m<=12;m++)
            foreach(int day in days)
            {
                if(y==last&&m>finalMonth)continue;
                var date=new DateTime(y,m,day);
                for(int i=0;i<120;i++)
                {
                    double open=price;
                    if(!altered)
                        price+=smoothUptrend?1.25:
                            0.85+Math.Sin((i+11*m)*0.13)*1.3;
                    // altered=true means a completely FLAT external
                    // market; all three directional example signals
                    // must fail, independently of the DEV approval stub.
                    bars.Add(new NQTimedBarV12(
                        date.AddHours(9).AddMinutes(30+i),
                        new NQBarV11(open,Math.Max(open,price)+0.55,
                            Math.Min(open,price)-0.55,price,
                            100+i%40)));
                }
                monthly[(y-first)*12+m-1]++;
            }
        var partition=first==2023?
            NQDataPartitionV16.ExternalValidation2023_2024:
            NQDataPartitionV16.FinalHoldout2025_2026;
        var manifest=new NQDataManifestV16(partition,"NQ DEC2026",
            "NT8_VISIBLE_SERIES_ASSUMED",
            altered?new string('b',64):
                smoothUptrend&&first==2025?new string('d',64):
                new string('c',64),
            new DateTime(first,1,1),new DateTime(last,12,31),
            new DateTime(first,1,1),new DateTime(last,12,31),
            bars.Count,bars.Count,monthly.Sum(),monthly);
        return new NQDataLoadV16(manifest,bars.AsReadOnly());
    }
    private static NQNativeFrozenCampaignV16 Campaign(
        NQNativeV20OosEvaluator evaluator,
        int[] families)
    {
        // This is an explicitly fabricated PASS fixture so the OOS
        // lock can be tested WITHOUT any fake winning DEV strategy.
        var selected=new NQPortfolioResultV13{
            Valid=true,Reason="SYNTHETIC_FIXTURE_ONLY"};
        var frozen=new List<NQFrozenCandidateV16>();
        for(int i=0;i<3;i++)
        {
            string id="SYNTH_STUB_"+i;
            selected.Selected.Add(new NQPortfolioCandidateV13(
                id,new List<NQG0RiskTradeV7>()));
            frozen.Add(new NQFrozenCandidateV16(id,
                Genes(families[i],12),
                NQNativeExitCanonicalV19.Analyze));
        }
        var stub=new NQIntegratedPortfolioRiskResultV15{
            Valid=true,ProvisionalPass=true,
            Selection=selected,
            Chronology=new NQChronologicalRiskResultV15{
                Valid=true,ProvisionalPass=true}
        };
        var development=new NQDataManifestV16(
            NQDataPartitionV16.Development2020_2022,
            "NQ DEC2026","NT8_VISIBLE_SERIES_ASSUMED",
            new string('a',64),new DateTime(2020,1,1),
            new DateTime(2022,12,31),new DateTime(2020,1,1),
            new DateTime(2022,12,31),86400,86400,288,
            Enumerable.Repeat(8,36).ToArray());
        return new NQNativeFrozenCampaignV16(
            development,stub,frozen,new NQChronologicalRiskConfigV15{
                MaxAccountStressDDUSD=2000,
                MaxSessionPeakToTroughUSD=1000,
                MaxConcurrentAdverseUSD=1000
            },8,new DateTime(2026,11,1),evaluator.Evaluate,
            "EXCANv19_1320_CONDITIONS_V20_OOS_SAME_V12_FILLS");
    }
    private static void Locked(Action action,string reason)
    {
        try{action();throw new Exception("WRONG_UNBLOCKED_"+reason);}
        catch(InvalidOperationException e)
        {A(e.Message.Contains(reason),
            "expected frozen lock "+reason+" got "+e.Message);}
    }
    private static int Direct(IList<NQTimedBarV12> rows,int index,
                              int type,int period)
    {
        // Deliberately independent from heldout cache: reconstruct the
        // completed RTH prefix of THIS specific day and time.
        var day=rows[index].Time.Date;
        var prefix=new List<NQBarV11>();
        for(int k=index;k>=0&&rows[k].Time.Date==day;k--)
            if(rows[k].Time.Hour*100+rows[k].Time.Minute>=930&&
               rows[k].Time.Hour*100+rows[k].Time.Minute<=1129)
                prefix.Add(rows[k].Bar);
        prefix.Reverse();
        bool bull,bear;
        if(!NQNativeConditionCatalogV19.TryEvaluate(
            prefix,type,period,out bull,out bear))return 0;
        A(!(bull&&bear),"direct cannot produce ambiguous signal");
        return bull?1:bear?-1:0;
    }
    public static int Main()
    {
        var external=Source(2023,2024);
        var reader=new NQNativeHeldoutSignalsV20(external.Bars,
            2023,2024,4*1024*1024);
        A(reader.RthBarCount==24*8*120&&reader.SessionCount==24*8,
          "2023–24 only full sessions, no 2020–22");
        // Compare independent historical V19 signal formulas including
        // new trend, momentum, volume, volatility and pattern families.
        int matches=0;
        for(int family=36;family<=119;family+=7)
          for(int periodIndex=0;periodIndex<2;periodIndex++)
          {
            int period=periodIndex==0?6:12;
            for(int i=0;i<external.Bars.Count;i+=137)
            {
                int cached=reader.GetSignal(i,family*11,period);
                int direct=Direct(external.Bars,i,family*11,period);
                A(cached==direct,
                  "OOS signal direct/cache mismatch family="+family);
                matches++;
            }
          }
        A(matches>2500,"thousands of OOS direct vs cached signals");
        A(reader.UsedBytes<=4*1024*1024&&reader.CacheHits>0,
          "bounded memory, reusable condition tables");
        var eva=new NQNativeV20OosEvaluator(4*1024*1024);
        int[] sample=Genes(99,12);
        var one=eva.Evaluate(external.Bars,sample,2023,2024);
        var two=NQNativeHistoricalEvaluatorV12.EvaluateHeldoutCustom(
            external.Bars,sample,2023,2024,
            (i,t,p)=>Direct(external.Bars,i,t,p),
            NQNativeExitCanonicalV19.Analyze);
        A(one.Valid&&two.Valid&&one.Trades.Count==two.Trades.Count &&
          one.Net==two.Net&&one.Score==
          NQNativeDiscoveryScoreV9.InvalidScore,
          "V19 external V12 fill model equals uncached and never trains V9");
        A(eva.SourceCacheBuilds==1,"one frozen shared OOS cache");
        A(!NQNativeHistoricalEvaluatorV12.EvaluateHeldout(
            external.Bars,sample,2023,2024).Valid,
          "legacy V11 frozen evaluator must reject new V19 IDs");
        var campaign=Campaign(eva,new[]{36,57,99});
        A(campaign.FreezeDigest.Length==64,
          "immutable versioned OOS digest for three V19 candidates");
        Locked(()=>campaign.EvaluateFinal(Source(2025,2026)),
            "FINAL_LOCKED_PENDING_EXTERNAL_PASS");
        var flatExternal=Source(2023,2024,true);
        var result=campaign.EvaluateExternal(flatExternal);
        A(result.Valid&&result.Candidates.Count==3&&
          result.Candidates.All(x=>
              x.CanonicalId.StartsWith("EXCANv19:")&&
              x.Economic!=null&&x.Economic.Valid)&&
          result.AccountRisk.Valid,
          "all 3 frozen V19 genomes evaluated on 2023–24 OOS");
        A(eva.SourceCacheBuilds==2,
          "three frozen candidates reused one new flat OOS cache");
        A(!result.ProvisionalPass && !campaign.ExternalAccepted,
          "synthetic external series MUST NOT fabricate winning portfolio");
        Locked(()=>campaign.EvaluateExternal(flatExternal),
            "EXTERNAL_REEVALUATION_FORBIDDEN");
        Locked(()=>campaign.EvaluateFinal(Source(2025,2026)),
            "FINAL_LOCKED_PENDING_EXTERNAL_PASS");
        var original=Campaign(new NQNativeV20OosEvaluator(
            4*1024*1024),new[]{36,57,99});
        var different=Campaign(new NQNativeV20OosEvaluator(
            4*1024*1024),new[]{36,57,100});
        A(original.FreezeDigest!=different.FreezeDigest,
          "any V19 frozen genome change produces different freeze SHA");
        // POSITIVE synthetic monotonic series: prove BOTH versioned OOS
        // partitions can be traversed once, in order, with exactly
        // the SAME frozen 3 EXCANv19 genes. This is contrived software QA
        // and NOT any evidence of NQ profitable strategies.
        var positiveEvaluator=new NQNativeV20OosEvaluator(4*1024*1024);
        var positive=Campaign(positiveEvaluator,new[]{36,37,38});
        var growingExternal=Source(2023,2024,false,true);
        var growingFinal=Source(2025,2026,false,true,10);
        A(growingFinal.Manifest.FullSessionsByMonth.Take(22)
            .All(x=>x==8)&&
          growingFinal.Manifest.FullSessionsByMonth.Skip(22)
            .All(x=>x==0),
          "final bars only 2025 Jan–2026 Oct");
        Locked(()=>positive.EvaluateFinal(growingFinal),
            "FINAL_LOCKED_PENDING_EXTERNAL_PASS");
        var approved=positive.EvaluateExternal(growingExternal);
        A(approved.Valid&&approved.ProvisionalPass&&
          positive.ExternalAccepted&&
          approved.Candidates.Count==3 &&
          approved.Candidates.All(x=>x.Economic.PeriodGatePass),
          "synthetic contrived uptrend allows the external success branch");
        var finished=positive.EvaluateFinal(growingFinal);
        A(finished.Valid&&finished.ProvisionalPass&&
          finished.Candidates.Count==3&&positive.FinalConsumed,
          "synthetic final branch unlocked ONLY after external approval");
        A(finished.EndExclusive==new DateTime(2026,11,1) &&
          approved.FreezeDigest==finished.FreezeDigest,
          "same 3 frozen genomes and 2026-Nov-01 cutoff");
        A(finished.Candidates.Zip(approved.Candidates,(a,b)=>
            a.Id==b.Id&&a.CanonicalId==b.CanonicalId).All(x=>x),
          "no mutations between external and final OOS");
        A(positiveEvaluator.SourceCacheBuilds==2,
          "one shared V19 signals cache per frozen OOS partition");
        Locked(()=>positive.EvaluateExternal(growingExternal),
            "EXTERNAL_REEVALUATION_FORBIDDEN");
        Locked(()=>positive.EvaluateFinal(growingFinal),
            "FINAL_HOLDOUT_REUSE_FORBIDDEN");

        // Detect contaminated non-OOS input before any OOS evaluator call.
        try
        {
            new NQNativeHeldoutSignalsV20(
                new List<NQTimedBarV12>{
                    new NQTimedBarV12(new DateTime(2022,1,1,9,30,0),
                        new NQBarV11(1,2,0.5,1,10))},
                2023,2024,1024);
            throw new Exception("ACCEPTED_2022_AS_OOS");
        }
        catch(ArgumentException) { }

        Console.WriteLine("NQ_V20_FROZEN_OOS_PASS "+
            "canonical=EXCANv19 frozen=3 directCachedMatches="+matches+
            " oosScore=NONE combinedChronology=TRUE"+
            " sourceCacheBuilds="+eva.SourceCacheBuilds+
            " oneShotExternal=TRUE finalLockedOnFail=TRUE"+
            " freezeDigestBound=TRUE"+
            " passingSyntheticExternalAndFinal=TRUE");
        Console.WriteLine("FROZEN_PORTFOLIO_PASS_WAS_SYNTHETIC_STUB_NOT_MARKET_DATA");
        return 0;
    }
}
