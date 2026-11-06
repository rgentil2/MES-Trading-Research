// S0.81 V20: read-only frozen EXCANv19 OOS evaluator.
// Source is passed ONLY after 3–5 candidates have passed DEV G0,
// portfolio M1 account risk and nested walk-forward, then frozen.
// Reuses a single bounded V19 cache for all portfolio members on a
// given OOS partition. Does not run optimizer or V9 discovery on OOS.
using System;
using System.Collections.Generic;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeV20OosEvaluator
    {
        private readonly long maxSignalBytes;
        private IList<NQTimedBarV12> currentSource;
        private NQNativeHeldoutSignalsV20 currentSignals;
        private int currentFirstYear,currentLastYear;
        public int SourceCacheBuilds{get;private set;}
        public NQNativeV20OosEvaluator(long maxSignalCacheBytes)
        {
            if(maxSignalCacheBytes<1024)
                throw new ArgumentOutOfRangeException("maxSignalCacheBytes");
            maxSignalBytes=maxSignalCacheBytes;
        }
        public NQHistoricalResultV12 Evaluate(
            IList<NQTimedBarV12> source,int[] frozenGenes,
            int firstYear,int lastYear)
        {
            // The external/final source is immutable from the caller's
            // perspective. This evaluator caches per-reference only.
            // The frozen campaign separately verifies manifest hashes.
            if(!Object.ReferenceEquals(currentSource,source)||
               currentFirstYear!=firstYear||currentLastYear!=lastYear)
            {
                currentSignals=new NQNativeHeldoutSignalsV20(source,
                    firstYear,lastYear,maxSignalBytes);
                currentSource=source;
                currentFirstYear=firstYear;
                currentLastYear=lastYear;
                SourceCacheBuilds++;
            }
            return NQNativeHistoricalEvaluatorV12.EvaluateHeldoutCustom(
                source,frozenGenes,firstYear,lastYear,
                currentSignals.GetSignal,NQNativeExitCanonicalV19.Analyze);
        }
    }
}
