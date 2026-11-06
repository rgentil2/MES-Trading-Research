// S0.82 V21 — bounded LRU of BASE NUMERICAL FEATURE VALUES by
// (formula family, period), shared across all 11 directional rules.
// Reduces repeated expensive V19 formula loops; legacy V11/V18 IDs
// delegate unchanged to original V14 signal cache.
// Same compressed 09:30–11:27 RTH V12 simulator and full-source ATR.
// Math uses only completed earlier bars: no peek at future bars.
// Budget bounds feature-array payload, not source, headers or GC.
using System;
using System.Collections.Generic;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeFeatureMemoV21
    {
        private sealed class Session
        {
            public readonly List<NQBarV11> Bars=new List<NQBarV11>();
            public readonly List<int> SourceIndices=new List<int>();
            public int FirstOrdinal;
        }
        private sealed class Table
        {
            public readonly double[] Values;
            public readonly LinkedListNode<long> Node;
            public Table(double[] values,LinkedListNode<long> node)
            {Values=values;Node=node;}
        }
        private readonly NQNativeSignalCacheV14 original;
        private readonly int[] ordinalBySource;
        private readonly int[] ordinalWithinDay;
        private readonly List<Session> sessions=new List<Session>();
        private readonly Dictionary<long,Table> tables=
            new Dictionary<long,Table>();
        private readonly LinkedList<long> age=new LinkedList<long>();
        private readonly long limitBytes;
        private readonly int rthCount;
        private long usedBytes;
        public long UsedBytes{get{return usedBytes;}}
        public long MaxBytes{get{return limitBytes;}}
        public int Entries{get{return tables.Count;}}
        public int FeatureBuilds{get;private set;}
        public int FeatureHits{get;private set;}
        public int Evictions{get;private set;}
        public int LegacyCalls{get;private set;}
        public int RthBars{get{return rthCount;}}

        public NQNativeFeatureMemoV21(NQNativeSignalCacheV14 source,
            long maxFeatureBytes)
        {
            if(source==null||maxFeatureBytes<1)
                throw new ArgumentException("V14 cache and memory cap required");
            original=source;
            var bars=source.Snapshot;
            ordinalBySource=new int[bars.Count];
            ordinalWithinDay=new int[bars.Count];
            for(int i=0;i<bars.Count;i++)
            {
                ordinalBySource[i]=-1;
                ordinalWithinDay[i]=-1;
            }
            DateTime currentDay=DateTime.MinValue,last=DateTime.MinValue;
            Session session=null;
            int ordinal=0;
            for(int i=0;i<bars.Count;i++)
            {
                var bar=bars[i];
                if(bar.Time<=last ||
                   (bar.Time.Year<2020||bar.Time.Year>2022))
                    throw new ArgumentException(
                        "V21 feature memo accepts only ordered 2020–22 development");
                last=bar.Time;
                if(currentDay!=bar.Time.Date)
                {
                    currentDay=bar.Time.Date;
                    session=new Session{FirstOrdinal=ordinal};
                    sessions.Add(session);
                }
                int minute=bar.Time.Hour*100+bar.Time.Minute;
                // Match V14 exactly: RTH cached signals exist until
                // 11:27, with 11:28/11:29 reserved for flatten.
                if(minute>=930&&minute<=1127)
                {
                    ordinalBySource[i]=ordinal++;
                    ordinalWithinDay[i]=session.Bars.Count;
                    session.Bars.Add(bar.Bar);
                    session.SourceIndices.Add(i);
                }
            }
            rthCount=ordinal;
            limitBytes=maxFeatureBytes;
            if(rthCount==0||8L*rthCount>limitBytes)
                throw new ArgumentException(
                    "Insufficient feature budget for one full RTH numeric table");
        }
        private static long Key(int family,int period)
        {return ((long)family<<32)|(uint)period;}
        private double[] Build(int family,int period)
        {
            var values=new double[rthCount];
            int warmup=NQNativeConditionCatalogV19.RequiredBars(period);
            foreach(var session in sessions)
            {
                // At first valid signal bar the V19 evaluator calculates
                // F(at), F(at-1), F(at-2). Thus the memo starts two bars
                // EARLIER than valid signal ordinal to support y and z
                // with unchanged formula warmup behavior.
                int begin=warmup-3;
                for(int k=0;k<session.Bars.Count;k++)
                {
                    int index=session.FirstOrdinal+k;
                    values[index]=Double.NaN;
                    if(k<begin)continue;
                    double x=NQNativeConditionCatalogV19.Feature(
                        session.Bars,k,family,period);
                    if(Double.IsNaN(x)||Double.IsInfinity(x))
                        throw new InvalidOperationException(
                            "V19 feature computed invalid floating number");
                    values[index]=x;
                }
            }
            return values;
        }

        public int GetSignal(int sourceIndex,int condition,int period)
        {
            if(sourceIndex<0||sourceIndex>=ordinalBySource.Length||
               condition<0||condition>=NQNativeConditionCatalogV19.Count||
               period<NQNativeConditionCatalogV19.MinPeriod||
               period>NQNativeConditionCatalogV19.MaxPeriod)
                throw new ArgumentOutOfRangeException("signal input");
            if(condition<NQNativeConditionCatalogV18.Count)
            {
                LegacyCalls++;
                return original.GetSignal(sourceIndex,condition,period);
            }
            int ordinal=ordinalBySource[sourceIndex];
            if(ordinal<0)return 0;
            int within=ordinalWithinDay[sourceIndex];
            if(within+1<NQNativeConditionCatalogV19.RequiredBars(period))
                return 0;
            int family=condition/NQNativeConditionCatalogV19.Rules;
            int rule=condition%NQNativeConditionCatalogV19.Rules;
            var values=AcquireValues(family,period);
            int state=NQNativeConditionCatalogV19.ResolveRule(
                values[ordinal],
                values[ordinal-1],
                values[ordinal-2],rule);
            if(state< -1||state>1)
                throw new InvalidOperationException("INVALID_CACHED_V19_RULE");
            return state;
        }
        // V24: obtain a completed-bar value table once per active
        // (family,period) for a candidate and reuse it across its M1
        // simulation. This avoids thousands of dictionary/LRU hits.
        // Returned arrays are read-only by contract (not enforced by
        // C# arrays); caller MUST NOT modify. An evicted table can remain
        // temporarily referenced by up to four active candidate leaves,
        // so the LRU limit only bounds resident dictionary payload.
        internal double[] AcquireValues(int family,int period)
        {
            if(family<36||family>=NQNativeConditionCatalogV19.Families||
               period<NQNativeConditionCatalogV19.MinPeriod||
               period>NQNativeConditionCatalogV19.MaxPeriod)
                throw new ArgumentOutOfRangeException("family/period");
            long key=Key(family,period);
            Table entry;
            if(!tables.TryGetValue(key,out entry))
            {
                var values=Build(family,period);
                long size=8L*values.Length;
                while(usedBytes+size>limitBytes&&age.Last!=null)
                {
                    long oldest=age.Last.Value;
                    usedBytes-=8L*tables[oldest].Values.Length;
                    tables.Remove(oldest);
                    age.RemoveLast();Evictions++;
                }
                var node=age.AddFirst(key);
                tables.Add(key,new Table(values,node));
                entry=tables[key];
                usedBytes+=size;FeatureBuilds++;
            }
            else
            {
                FeatureHits++;
                age.Remove(entry.Node);age.AddFirst(entry.Node);
            }
            return entry.Values;
        }
        internal int SourceOrdinal(int sourceIndex)
        {
            if(sourceIndex<0||sourceIndex>=ordinalBySource.Length)
                throw new ArgumentOutOfRangeException("sourceIndex");
            return ordinalBySource[sourceIndex];
        }
        internal int SourceRthWithinDay(int sourceIndex)
        {
            if(sourceIndex<0||sourceIndex>=ordinalWithinDay.Length)
                throw new ArgumentOutOfRangeException("sourceIndex");
            return ordinalWithinDay[sourceIndex];
        }

        public NQHistoricalResultV12 Evaluate(int[] genes)
        {
            return original.EvaluateExpandedWithSignalProvider(
                genes,NQNativeExitCanonicalV19.Analyze,GetSignal);
        }
    }
}
