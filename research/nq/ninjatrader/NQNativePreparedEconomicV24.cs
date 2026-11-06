// S0.85 V24 ONLY: speed up long-horizon FULL V12 M1 economic
// backtests. Prepare up to four numeric family/period tables once
// per EXCANv19 genome and fetch completed signal states by ordinal.
// Identical V12 costs, SL-first intraminute ambiguity, ATR, fills,
// score V9, Boolean rules and 2020–22 development restriction.
// Pure C#, never reaches 2023+ or any NinjaTrader order methods.
using System;
using System.Collections.Generic;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativePreparedEconomicV24
    {
        private sealed class Leaf
        {
            public int Condition,Period,Rule,RequiredBars;
            public double[] Values;
        }
        private readonly NQNativeSignalCacheV14 source;
        private readonly NQNativeFeatureMemoV21 features;
        public int PreparedGenomes{get;private set;}
        public int PreparedNumericLeaves{get;private set;}
        public int LegacyLeafCalls{get;private set;}
        public NQNativePreparedEconomicV24(
            NQNativeSignalCacheV14 historical,
            NQNativeFeatureMemoV21 featureMemo)
        {
            if(historical==null||featureMemo==null||
               !featureMemo.SharesSource(historical))
                throw new ArgumentException(
                    "V24_REQUIRES_MATCHED_V14_AND_V21_RESEARCH_SOURCE");
            source=historical;features=featureMemo;
        }
        public NQHistoricalResultV12 Evaluate(int[] genes)
        {
            var canonical=NQNativeExitCanonicalV19.Analyze(genes);
            if(canonical.IsRedundant)
                return new NQHistoricalResultV12{
                    Valid=false,Reason="REDUNDANT_BOOLEAN",
                    Score=NQNativeDiscoveryScoreV9.InvalidScore};
            var leaves=new List<Leaf>(genes[0]);
            for(int k=0;k<genes[0];k++)
            {
                int type=genes[1+2*k],period=genes[2+2*k];
                // Pin at most 4 arrays for the duration of this
                // candidate; numeric LRU may evict a table from its
                // dictionary, but pinned read-only arrays stay valid.
                var x=new Leaf{
                    Condition=type,Period=period,
                    Rule=type%NQNativeConditionCatalogV19.Rules,
                    RequiredBars=NQNativeConditionCatalogV19.RequiredBars(period)
                };
                if(type>=NQNativeConditionCatalogV18.Count)
                {
                    int family=type/NQNativeConditionCatalogV19.Rules;
                    x.Values=features.AcquireValues(family,period);
                    PreparedNumericLeaves++;
                }
                leaves.Add(x);
            }
            PreparedGenomes++;
            return source.EvaluateExpandedWithSignalProvider(genes,
                NQNativeExitCanonicalV19.Analyze,
                (index,type,period)=>
                {
                    Leaf match=null;
                    for(int k=0;k<leaves.Count;k++)
                        if(leaves[k].Condition==type&&
                           leaves[k].Period==period)
                        {match=leaves[k];break;}
                    if(match==null)
                        throw new InvalidOperationException(
                            "V24_SIGNAL_LEAF_NOT_PREPARED");
                    if(match.Values==null)
                    {
                        LegacyLeafCalls++;
                        return features.GetSignal(index,type,period);
                    }
                    int ordinal=features.SourceOrdinal(index);
                    if(ordinal<0)return 0;
                    if(features.SourceRthWithinDay(index)+1<
                       match.RequiredBars)return 0;
                    int direction=NQNativeConditionCatalogV19.ResolveRule(
                        match.Values[ordinal],
                        match.Values[ordinal-1],
                        match.Values[ordinal-2],
                        match.Rule);
                    if(direction< -1||direction>1)
                        throw new InvalidOperationException(
                            "V24_NUMERIC_SIGNAL_INVALID");
                    return direction;
                });
        }
    }
}
