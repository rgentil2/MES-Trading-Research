// S0.75 — time-ordered research portfolio M1 mark-to-market risk.
// Reads EXECUTED conservative V12 fill ledger (entry/exit prices) and
// NQ one-minute OHLCV; does NOT claim tick-sequenced fills, real NT8 parity,
// official MFFU trailing-account compliance or actual out-of-sample returns.
// Each ledger timestamp refers to the original bar timestamp. We apply
// fills BEFORE that bar's close mark and do not invent unseen intraminute
// paths. Stress DD assumes adverse high/low ordering within each minute.
// Research 2020–22 only. No live entry, stop or target submission here.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQChronologicalRiskConfigV15
    {
        public double MaxAccountStressDDUSD=2000.0;
        public double MaxSessionPeakToTroughUSD=1000.0;
        public double MaxConcurrentAdverseUSD=1000.0;
        public double PointValueUSD=20.0;

        public void Validate()
        {
            if(!(MaxAccountStressDDUSD>0) ||
               !(MaxSessionPeakToTroughUSD>0) ||
               !(MaxConcurrentAdverseUSD>0) ||
               !(PointValueUSD>0) ||
               Double.IsNaN(MaxAccountStressDDUSD) ||
               Double.IsInfinity(MaxAccountStressDDUSD) ||
               Double.IsNaN(MaxSessionPeakToTroughUSD) ||
               Double.IsInfinity(MaxSessionPeakToTroughUSD) ||
               Double.IsNaN(MaxConcurrentAdverseUSD) ||
               Double.IsInfinity(MaxConcurrentAdverseUSD) ||
               Double.IsNaN(PointValueUSD) ||
               Double.IsInfinity(PointValueUSD))
                throw new ArgumentException("Invalid provisional M1 risk config");
        }
    }

    public sealed class NQChronologicalRiskResultV15
    {
        public bool Valid,ProvisionalPass;
        public string Reason;
        public double RealizedNetUSD,MaxClosedDDUSD;
        public double MaxM1CloseMarkedDDUSD;
        public double MaxAdversarialM1StressDDUSD;
        public double MaxSessionPeakToTroughUSD;
        public double MaxConcurrentAdverseUSD;
        public int MaxConcurrentContracts,Marks;
        public int FillCount,SessionPauseBreaches,AccountDDBreaches;
    }

    public static class NQNativeChronologicalRiskV15
    {
        private static bool Finite(double x)
        {return !Double.IsNaN(x)&&!Double.IsInfinity(x);}
        private static NQChronologicalRiskResultV15 Fail(string why)
        {return new NQChronologicalRiskResultV15{Valid=false,Reason=why};}

        public static NQChronologicalRiskResultV15 Evaluate(
            IList<NQTimedBarV12> source,
            IList<NQExecutionFillV12> fills,
            NQChronologicalRiskConfigV15 cfg)
        {
            return EvaluateCore(source,fills,cfg,2020,2022);
        }

        // Only externally frozen portfolios may use this entrypoint.
        // It shares exactly the same M1 risk loop but never accepts
        // 2020–22 as a holdout. Does not expose GA or candidate tuning.
        public static NQChronologicalRiskResultV15 EvaluateHeldout(
            IList<NQTimedBarV12> source,
            IList<NQExecutionFillV12> fills,
            NQChronologicalRiskConfigV15 cfg,int firstYear,int lastYear)
        {
            if(!((firstYear==2023&&lastYear==2024)||
                 (firstYear==2025&&lastYear==2026)))
                return Fail("ONLY_FROZEN_EXTERNAL_OR_FINAL_YEARS");
            return EvaluateCore(source,fills,cfg,firstYear,lastYear);
        }

        private static NQChronologicalRiskResultV15 EvaluateCore(
            IList<NQTimedBarV12> source,
            IList<NQExecutionFillV12> fills,
            NQChronologicalRiskConfigV15 cfg,int firstYear,int lastYear)
        {
            if(source==null||source.Count==0||fills==null||cfg==null)
                return Fail("NULL_OR_EMPTY");
            cfg.Validate();
            var byTimestamp=new Dictionary<DateTime,int>();
            for(int i=0;i<source.Count;i++)
            {
                if(source[i]==null||source[i].Time.Year<firstYear||
                   source[i].Time.Year>lastYear||
                   i>0&&source[i].Time<=source[i-1].Time)
                    return Fail("INVALID_OR_OUT_OF_SAMPLE_BARS");
                byTimestamp.Add(source[i].Time,i);
            }
            var exits=new List<NQExecutionFillV12>[source.Count];
            var entries=new List<NQExecutionFillV12>[source.Count];
            foreach(var f in fills)
            {
                if(f==null||f.Side!=1&&f.Side!=-1||
                   f.Quantity<1||f.Quantity>5||
                   !Finite(f.EntryPrice)||f.EntryPrice<=0||
                   !Finite(f.ExitPrice)||f.ExitPrice<=0||
                   !Finite(f.RoundTripFeesUSD)||f.RoundTripFeesUSD<0||
                   f.EntryTime>f.ExitTime ||
                   f.EntryTime.Date!=f.ExitTime.Date)
                    return Fail("INVALID_EXECUTION_LEDGER");
                int ei,xi;
                if(!byTimestamp.TryGetValue(f.EntryTime,out ei) ||
                   !byTimestamp.TryGetValue(f.ExitTime,out xi))
                    return Fail("MISSING_ENTRY_OR_EXIT_BAR");
                if(xi<ei||xi-ei!=
                    (int)(f.ExitTime-f.EntryTime).TotalMinutes)
                    return Fail("MISSING_INTRATRADE_MINUTE");
                if(entries[ei]==null)entries[ei]=new List<NQExecutionFillV12>();
                if(exits[xi]==null)exits[xi]=new List<NQExecutionFillV12>();
                entries[ei].Add(f);exits[xi].Add(f);
            }

            var active=new List<NQExecutionFillV12>();
            var result=new NQChronologicalRiskResultV15{
                Valid=true,Reason="M1_CLOSE_AND_ADVERSE_EXTREME_PROXY_ONLY",
                FillCount=fills.Count
            };
            double realized=0,closedPeak=0,closePeak=0,stressPeak=0;
            double dayOpening=0,dayPeak=0;
            DateTime day=DateTime.MinValue;
            bool dailyPauseTriggered=false,ddTriggered=false;

            for(int i=0;i<source.Count;i++)
            {
                var item=source[i];
                if(item.Time.Date!=day)
                {
                    if(active.Count!=0)
                        return Fail("OVERNIGHT_OPEN_POSITION");
                    day=item.Time.Date;
                    dayOpening=realized;
                    dayPeak=realized;
                    dailyPauseTriggered=false;
                }

                // Entries/exits sharing a bar are permitted. Their recorded
                // fill is realized at that bar timestamp; we cannot infer
                // a unique M1 intrabar sequence from those timestamps.
                if(entries[i]!=null)active.AddRange(entries[i]);
                if(exits[i]!=null)
                    foreach(var f in exits[i])
                    {
                        if(!active.Remove(f))
                            return Fail("EXIT_WITHOUT_OPEN_POSITION");
                        realized+=(f.ExitPrice-f.EntryPrice)*
                            cfg.PointValueUSD*f.Side*f.Quantity-
                            f.RoundTripFeesUSD;
                    }

                double marked=realized,adverse=realized,favorable=realized;
                double concurrentAdverse=0;
                int contracts=0;
                foreach(var f in active)
                {
                    contracts+=f.Quantity;
                    double fee=f.RoundTripFeesUSD;
                    double close=(item.Bar.Close-f.EntryPrice)*
                        cfg.PointValueUSD*f.Side*f.Quantity-fee;
                    double worst=(f.Side>0?item.Bar.Low-f.EntryPrice:
                        f.EntryPrice-item.Bar.High)*
                        cfg.PointValueUSD*f.Quantity-fee;
                    double best=(f.Side>0?item.Bar.High-f.EntryPrice:
                        f.EntryPrice-item.Bar.Low)*
                        cfg.PointValueUSD*f.Quantity-fee;
                    marked+=close;
                    adverse+=worst;
                    favorable+=best;
                    concurrentAdverse+=Math.Max(0,-worst);
                }
                result.MaxConcurrentContracts=Math.Max(
                    result.MaxConcurrentContracts,contracts);
                result.MaxConcurrentAdverseUSD=Math.Max(
                    result.MaxConcurrentAdverseUSD,concurrentAdverse);

                closedPeak=Math.Max(closedPeak,realized);
                result.MaxClosedDDUSD=Math.Max(result.MaxClosedDDUSD,
                    closedPeak-realized);

                closePeak=Math.Max(closePeak,marked);
                result.MaxM1CloseMarkedDDUSD=Math.Max(
                    result.MaxM1CloseMarkedDDUSD,closePeak-marked);

                // Unknown high/low chronological order: assume favorable
                // extreme may set a peak BEFORE the adverse extreme.
                stressPeak=Math.Max(stressPeak,favorable);
                result.MaxAdversarialM1StressDDUSD=Math.Max(
                    result.MaxAdversarialM1StressDDUSD,stressPeak-adverse);

                dayPeak=Math.Max(dayPeak,favorable);
                double sessionLoss=dayPeak-adverse;
                result.MaxSessionPeakToTroughUSD=Math.Max(
                    result.MaxSessionPeakToTroughUSD,sessionLoss);
                // Also measure loss from session start even when earlier
                // gains in the same session are not yet realized.
                sessionLoss=Math.Max(sessionLoss,dayOpening-adverse);
                if(!dailyPauseTriggered &&
                   sessionLoss>=cfg.MaxSessionPeakToTroughUSD)
                {
                    result.SessionPauseBreaches++;
                    dailyPauseTriggered=true;
                }
                if(!ddTriggered &&
                   result.MaxAdversarialM1StressDDUSD>=
                   cfg.MaxAccountStressDDUSD)
                {
                    result.AccountDDBreaches++;
                    ddTriggered=true;
                }
                result.Marks++;
            }
            if(active.Count!=0)return Fail("UNCLOSED_POSITION_AT_END");
            result.RealizedNetUSD=realized;
            result.ProvisionalPass=
                result.MaxAdversarialM1StressDDUSD<
                    cfg.MaxAccountStressDDUSD &&
                result.MaxSessionPeakToTroughUSD<
                    cfg.MaxSessionPeakToTroughUSD &&
                result.MaxConcurrentAdverseUSD<
                    cfg.MaxConcurrentAdverseUSD;
            return result;
        }
    }
}
