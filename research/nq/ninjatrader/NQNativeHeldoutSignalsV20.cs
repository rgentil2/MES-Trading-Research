// V20 — read-only, bounded completed-bar V19 condition cache for
// frozen external 2023–24 or final 2025–26 datasets. NO GA, NO
// optimization callbacks, NO access to 2020–22 development. Each
// conditional table is computed solely from bars ALREADY COMPLETED in
// the same RTH session. User's NinjaTrader NQ DEC2026 is the eventual
// final validation source; no contract/rollover auditing here.
using System;
using System.Collections.Generic;
using System.Linq;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeHeldoutSignalsV20
    {
        private sealed class Session
        {
            public readonly List<NQBarV11> Bars=new List<NQBarV11>();
        }
        private sealed class Cached
        {
            public readonly byte[] Values;
            public readonly LinkedListNode<long> Node;
            public Cached(byte[] values,LinkedListNode<long> node)
            {Values=values;Node=node;}
        }
        private readonly Session[] sessions;
        private readonly int[] rthIndexBySource;
        private readonly int barCount;
        private readonly long maxBytes;
        private readonly Dictionary<long,Cached> tables=
            new Dictionary<long,Cached>();
        private readonly LinkedList<long> lru=new LinkedList<long>();
        private long used;
        public int Computations{get;private set;}
        public int CacheHits{get;private set;}
        public int Evictions{get;private set;}
        public long UsedBytes{get{return used;}}
        public int SessionCount{get{return sessions.Length;}}
        public int RthBarCount{get{return barCount;}}

        public NQNativeHeldoutSignalsV20(IList<NQTimedBarV12> source,
            int firstYear,int lastYear,long maximumCacheBytes)
        {
            if(source==null||source.Count==0||
               !((firstYear==2023&&lastYear==2024)||
                 (firstYear==2025&&lastYear==2026))||
               maximumCacheBytes<source.Count/2)
                throw new ArgumentException(
                    "OOS-only M1 data and positive bounded cache");
            var dayList=new List<Session>();
            var index=new int[source.Count];
            for(int k=0;k<index.Length;k++)index[k]=-1;
            DateTime previous=DateTime.MinValue,day=DateTime.MinValue;
            Session current=null;
            int rthIndex=0;
            for(int i=0;i<source.Count;i++)
            {
                var row=source[i];
                if(row==null||row.Time.Year<firstYear||
                   row.Time.Year>lastYear||
                   row.Time<=previous||
                   i>0&&row.Time-previous>TimeSpan.FromDays(5))
                    throw new ArgumentException("OOS_INVALID_OR_MIXED_SOURCE");
                previous=row.Time;
                if(row.Time.Date!=day)
                {
                    day=row.Time.Date;
                    current=new Session();
                    dayList.Add(current);
                }
                int hhmm=row.Time.Hour*100+row.Time.Minute;
                if(hhmm>=930&&hhmm<=1129)
                {
                    index[i]=rthIndex++;
                    current.Bars.Add(row.Bar);
                }
            }
            rthIndexBySource=index;
            sessions=dayList.ToArray();
            barCount=rthIndex;
            maxBytes=maximumCacheBytes;
            if(barCount==0||barCount>maximumCacheBytes)
                throw new ArgumentException("Not enough bounded cache for one RTH table");
        }
        private static long Key(int type,int period)
        {return ((long)type<<32)|(uint)period;}

        private byte[] Build(int type,int period)
        {
            var all=new byte[barCount];
            int used=0,needed=NQNativeConditionCatalogV19.RequiredBars(period);
            foreach(var session in sessions)
            {
                var partial=new List<NQBarV11>();
                foreach(var candle in session.Bars)
                {
                    partial.Add(candle);
                    if(partial.Count>=needed)
                    {
                        bool bull,bear;
                        if(!NQNativeConditionCatalogV19.TryEvaluate(
                              partial,type,period,out bull,out bear)||
                           bull&&bear)
                            throw new InvalidOperationException(
                                "NONFINITE_OR_AMBIGUOUS_V19_HOLDOUT_SIGNAL");
                        all[used]=bull?(byte)1:bear?(byte)2:(byte)0;
                    }
                    used++;
                }
            }
            if(used!=barCount)
                throw new InvalidOperationException("RTH_SIGNAL_INDEX_MISMATCH");
            return all;
        }

        public int GetSignal(int sourceIndex,int type,int period)
        {
            if(sourceIndex<0||sourceIndex>=rthIndexBySource.Length||
               type<0||type>=NQNativeConditionCatalogV19.Count||
               period<NQNativeConditionCatalogV19.MinPeriod||
               period>NQNativeConditionCatalogV19.MaxPeriod)
                throw new ArgumentOutOfRangeException("sourceIndex/type/period");
            int ordinal=rthIndexBySource[sourceIndex];
            if(ordinal<0)return 0;
            long key=Key(type,period);
            Cached table;
            if(!tables.TryGetValue(key,out table))
            {
                byte[] values=Build(type,period);
                while(used+values.Length>maxBytes&&lru.Last!=null)
                {
                    long evict=lru.Last.Value;
                    used-=tables[evict].Values.Length;
                    tables.Remove(evict);
                    lru.RemoveLast();
                    Evictions++;
                }
                var node=lru.AddFirst(key);
                table=new Cached(values,node);
                tables.Add(key,table);
                used+=values.Length;
                Computations++;
            }
            else
            {
                CacheHits++;
                lru.Remove(table.Node);
                lru.AddFirst(table.Node);
            }
            byte v=table.Values[ordinal];
            return v==1?1:v==2?-1:0;
        }
    }
}
