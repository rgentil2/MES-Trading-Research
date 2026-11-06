// S0.74 — bounded, lazy, LRU signal cache for independent NQ M1 research.
// An immutable VALIDATED 2020–22 source snapshot is used for every run.
// Stores one unsigned byte per actual RTH signal bar per (condition,period).
// 0 neutral/unready, 1 bull, 2 bear. No lookahead: each session's prefix
// is grown one completed bar at a time. Does not cache or replay fills.
// Cache is shared across GA candidates; budget bounds signal tables, NOT
// the fixed source copy, session indexes, C# overhead or managed GC.
// Research-only; NOT a NinjaTrader historical fill parity claim.
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeSignalCacheV14
    {
        private sealed class Session
        {
            public readonly List<NQBarV11> Bars=new List<NQBarV11>();
        }
        private sealed class Table
        {
            public readonly byte[] Signal;
            public readonly LinkedListNode<long> Node;
            public Table(byte[] signal,LinkedListNode<long> node)
            {Signal=signal;Node=node;}
        }

        private readonly object gate=new object();
        private readonly Dictionary<long,Table> tables=new Dictionary<long,Table>();
        private readonly LinkedList<long> age=new LinkedList<long>();
        private readonly List<Session> sessions=new List<Session>();
        private readonly int[] rthOrdinalBySource;
        private readonly ReadOnlyCollection<NQTimedBarV12> snapshot;
        private readonly int signalBytesPerTable;
        private readonly long maxCacheBytes;
        private long usedCacheBytes;
        private int hits,misses,evictions;

        private static int HHmmss(DateTime t)
        {return t.Hour*10000+t.Minute*100+t.Second;}

        public NQNativeSignalCacheV14(IList<NQTimedBarV12> source,
                                      long maxSignalCacheBytes)
        {
            if(source==null||source.Count==0)
                throw new ArgumentException("Nonempty source required");
            if(maxSignalCacheBytes<1)
                throw new ArgumentOutOfRangeException("maxSignalCacheBytes");
            maxCacheBytes=maxSignalCacheBytes;
            var copy=new NQTimedBarV12[source.Count];
            rthOrdinalBySource=new int[source.Count];
            for(int i=0;i<rthOrdinalBySource.Length;i++)
                rthOrdinalBySource[i]=-1;
            DateTime last=DateTime.MinValue;
            DateTime day=DateTime.MinValue;
            int rthOrdinal=0;
            Session session=null;
            for(int i=0;i<source.Count;i++)
            {
                var item=source[i];
                if(item==null||item.Time.Year<2020||item.Time.Year>2022||
                   item.Time<=last||
                   i>0 && item.Time-last>TimeSpan.FromDays(5))
                    throw new ArgumentException(
                        "Invalid, unordered, >5-day gap or held-out 2023+ bar");
                // NQTimedBarV12 and NQBarV11 contain immutable data.
                copy[i]=new NQTimedBarV12(item.Time,item.Bar);
                last=item.Time;
                if(item.Time.Date!=day)
                {
                    day=item.Time.Date;
                    session=new Session();
                    sessions.Add(session);
                }
                int hh=HHmmss(item.Time);
                if(hh>=93000&&hh<=112700)
                {
                    rthOrdinalBySource[i]=rthOrdinal++;
                    session.Bars.Add(item.Bar);
                }
            }
            signalBytesPerTable=rthOrdinal;
            if(signalBytesPerTable==0)
                throw new ArgumentException("No RTH 09:30-11:27 M1 bars");
            if(signalBytesPerTable>maxCacheBytes)
                throw new ArgumentException(
                    "Cache cap too small to store one full RTH signal table");
            snapshot=Array.AsReadOnly(copy);
        }

        public IList<NQTimedBarV12> Snapshot {get{return snapshot;}}
        public int SourceBars {get{return snapshot.Count;}}
        public int RthBars {get{return signalBytesPerTable;}}
        public long MaxSignalBytes {get{return maxCacheBytes;}}
        public int Entries {get{lock(gate)return tables.Count;}}
        public long UsedSignalBytes {get{lock(gate)return usedCacheBytes;}}
        public int CacheHits {get{lock(gate)return hits;}}
        public int CacheMisses {get{lock(gate)return misses;}}
        public int CacheEvictions {get{lock(gate)return evictions;}}

        private static long Key(int condition,int period)
        {
            return ((long)condition<<32)|(uint)period;
        }

        private byte[] Calculate(int condition,int period)
        {
            var signal=new byte[signalBytesPerTable];
            int needed=NQNativeConditionsV11.RequiredBars(period);
            int offset=0;
            foreach(Session s in sessions)
            {
                var prefix=new List<NQBarV11>(s.Bars.Count);
                foreach(NQBarV11 bar in s.Bars)
                {
                    prefix.Add(bar);
                    if(prefix.Count>=needed)
                    {
                        bool bull,bear;
                        if(!NQNativeConditionsV11.TryEvaluate(prefix,condition,
                                period,out bull,out bear) || bull&&bear)
                            throw new InvalidOperationException(
                                "Nonfinite, invalid or ambiguous condition");
                        signal[offset]=bull?(byte)1:bear?(byte)2:(byte)0;
                    }
                    offset++;
                }
            }
            if(offset!=signal.Length)
                throw new InvalidOperationException("RTH cache offset mismatch");
            return signal;
        }

        private byte[] Ensure(int condition,int period)
        {
            if(condition<0||condition>=NQNativeConditionsV11.Count ||
               period<NQNativeConditionsV11.MinPeriod ||
               period>NQNativeConditionsV11.MaxPeriod)
                throw new ArgumentOutOfRangeException("condition/period");

            long id=Key(condition,period);
            lock(gate)
            {
                Table current;
                if(tables.TryGetValue(id,out current))
                {
                    hits++;
                    age.Remove(current.Node);
                    age.AddFirst(current.Node);
                    return current.Signal;
                }

                // Compute while holding one lock: no duplicated builds and
                // bounded peak signal arrays across concurrent clients.
                byte[] newSignals=Calculate(condition,period);
                while(usedCacheBytes+newSignals.Length>maxCacheBytes &&
                      age.Last!=null)
                {
                    long oldest=age.Last.Value;
                    var drop=tables[oldest];
                    usedCacheBytes-=drop.Signal.Length;
                    tables.Remove(oldest);
                    age.RemoveLast();
                    evictions++;
                }
                var node=new LinkedListNode<long>(id);
                age.AddFirst(node);
                tables.Add(id,new Table(newSignals,node));
                usedCacheBytes+=newSignals.Length;
                misses++;
                return newSignals;
            }
        }

        // Signature matches V12 EvaluateWithSignals callback. Safe outside
        // RTH: zero means neutral. Checks bounds even for non-RTH indices.
        public int GetSignal(int sourceIndex,int condition,int period)
        {
            if(sourceIndex<0||sourceIndex>=rthOrdinalBySource.Length)
                throw new ArgumentOutOfRangeException("sourceIndex");
            int rth=rthOrdinalBySource[sourceIndex];
            if(rth<0)return 0;
            byte s=Ensure(condition,period)[rth];
            return s==1?1:s==2?-1:0;
        }

        public NQHistoricalResultV12 Evaluate(int[] genes)
        {
            // Exactly the V12 position, SL/TP, time-exit and V9 fitness
            // calculation, with cached directional leaves only.
            return NQNativeHistoricalEvaluatorV12.EvaluateWithSignals(
                snapshot,genes,GetSignal,true);
        }
    }

    public sealed class NQNativeCachedPipelineV14
    {
        private readonly NQNativeSignalCacheV14 cache;
        private readonly NQEvolutionConfigV12 cfg;
        private readonly int[] baseline;
        private readonly bool exploreExits;
        public NQNativeSignalCacheV14 Cache{get{return cache;}}
        public NQNativeCachedPipelineV14(IList<NQTimedBarV12> bars,
            int[] genes,NQEvolutionConfigV12 config,bool explore,
            bool requireFull36Months,long maxSignalCacheBytes)
        {
            if(genes==null||genes.Length!=20||config==null)
                throw new ArgumentException("Need baseline 20 genes and GA config");
            baseline=(int[])genes.Clone();
            cfg=config;exploreExits=explore;
            cache=new NQNativeSignalCacheV14(bars,maxSignalCacheBytes);
            if(requireFull36Months)
            {
                bool[] covered=new bool[36];
                foreach(var b in cache.Snapshot)
                    covered[(b.Time.Year-2020)*12+b.Time.Month-1]=true;
                if(covered.Any(x=>!x))
                    throw new InvalidOperationException(
                        "Missing at least one 2020-22 development month");
            }
        }
        public NQEvolutionSummaryV12 Run()
        {
            var search=new NQEvolutionEngineV12(
                NQEvolutionEngineV12.DefaultDomains(baseline,exploreExits),
                cfg);
            return search.Run(g=>cache.Evaluate(g.Genes).Score);
        }
    }
}
