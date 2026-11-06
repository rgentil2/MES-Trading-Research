// NQ S0.68 — V8 AUDIT OBSERVER for NinjaTrader 8 (M1, 2020-2022).
// REQUIRES the existing NQNativeGeneticLabV5 and its helper dependencies.
// Preserves V5 order logic by calling base.OnBarUpdate() exactly once.
// It adds a separate, non-trading replay of signal criteria and 1-minute
// CLOSE-marked strategy equity. It DOES NOT generate new/extra orders.
// No tick chronology; no full intrabar/trailing-funded-account claim.
// Use ONLY in Strategy Analyzer historical backtests, NOT on a live chart.
// Verify the same 20 seed-20261102 candidate PnL/trade counts as V5 first.
using System;
using System.ComponentModel;
using System.Globalization;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    public class NQNativeGeneticLabV8Audit : NQNativeGeneticLabV5
    {
        // Counter semantics: every bar counted once when relevant.
        private const int KBar=0, Window=1, Warm=2, Raw=3,
            NoDirection=4, BlockPosition=5, BlockDailyCount=6,
            BlockATR=7, BlockStopBudget=8, BlockDailyLoss=9,
            EligibleSubmit=10, InvalidGenes=11;
        private static readonly string[] MetricNames={
            "m1Bars","signalWindowBars","afterWarmup","rawDirectional",
            "noDirection","blockedPosition","blockedDailyCount",
            "blockedATR","blockedStopBudget","blockedDailyLoss",
            "predictedSubmissions","invalidGenes"
        };
        private readonly int[,] y = new int[3,12];
        private readonly int[,] month = new int[36,3]; // raw,predicted,real fills
        private DateTime auditDay=DateTime.MinValue;
        private int auditDayBars,auditDaySubmissions;
        private double auditDayStartClosed;
        private bool equityReady;
        private double equityPeak,closeDDMax;
        private double[] yPeak=new double[3],yCloseDD=new double[3],
                         yDailyDD=new double[3],yWorstDaily=new double[3];
        private bool[] ySeen=new bool[3];
        private DateTime markedDay=DateTime.MinValue;
        private double dailyStartEquity,dailyPeak;
        private bool dailyReady;
        private int sampledBars,nonFiniteEquityCount,actualTrades;

        protected override void OnStateChange()
        {
            base.OnStateChange(); // keep V5 parameters, ATR exit and canonical logic
            if(State==State.SetDefaults)
            {
                Name="NQNativeGeneticLabV8Audit";
                Description="V5 unchanged order execution + V8 historical M1 frequency and bar-close equity diagnostics only.";
                // No additional NinjaScriptProperty optimizer gene is introduced.
            }
            else if(State==State.DataLoaded)
            {
                Array.Clear(y,0,y.Length);
                Array.Clear(month,0,month.Length);
                Array.Clear(yPeak,0,yPeak.Length);
                Array.Clear(yCloseDD,0,yCloseDD.Length);
                Array.Clear(yDailyDD,0,yDailyDD.Length);
                Array.Clear(yWorstDaily,0,yWorstDaily.Length);
                Array.Clear(ySeen,0,ySeen.Length);
                auditDay=DateTime.MinValue; markedDay=DateTime.MinValue;
                auditDayBars=0; auditDaySubmissions=0;
                equityReady=false; dailyReady=false;
                sampledBars=0; nonFiniteEquityCount=0; actualTrades=0;
                closeDDMax=0; equityPeak=0;
            }
            else if(State==State.Terminated && sampledBars>0)
            {
                V8Report();
            }
        }

        // The live order path is *always* V5's; no Enter/Exit/SetStop here.
        protected override void OnBarUpdate()
        {
            base.OnBarUpdate();
            if(State!=State.Historical || BarsInProgress!=0 ||
               BarsPeriod.BarsPeriodType!=BarsPeriodType.Minute ||
               BarsPeriod.Value!=1 ||
               Instrument.MasterInstrument.Name!="NQ" ||
               CurrentBar<0 || Time[0].Year<2020 || Time[0].Year>2022)
                return;
            int yi=Time[0].Year-2020;
            int mi=yi*12+Time[0].Month-1;

            // V5 resets its bar counter on change of session Date.
            if(Time[0].Date!=auditDay)
            {
                auditDay=Time[0].Date;
                auditDayBars=0;
                auditDaySubmissions=0;
                auditDayStartClosed=SystemPerformance.AllTrades
                    .TradesPerformance.Currency.CumProfit;
            }
            else auditDayBars++;

            y[yi,KBar]++;
            V8MarkEquity(yi);

            if(CurrentBar<3)return;
            int time=ToTime(Time[0]);
            if(time<93500 || time>112700)return;
            y[yi,Window]++;

            if(!ValidGenes())
            {
                y[yi,InvalidGenes]++;
                return;
            }
            int warm=NeededBarsAudit(AType,APeriod);
            if(ConditionCount>=2)warm=Math.Max(warm,NeededBarsAudit(BType,BPeriod));
            if(ConditionCount>=3)warm=Math.Max(warm,NeededBarsAudit(CType,CPeriod));
            if(ConditionCount>=4)warm=Math.Max(warm,NeededBarsAudit(DType,DPeriod));
            if(ExitMode>0)warm=Math.Max(warm,ATRPeriod+4);
            if(auditDayBars<warm)return;
            y[yi,Warm]++;

            // AUDIT ONLY: evaluate raw V5-equivalent indicators even if an
            // open position or a risk gate would later reject an entry.
            // This cannot be inferred from the closed-trade list alone.
            bool bull,bear;
            SlotAudit(AType,APeriod,out bull,out bear);
            if(ConditionCount>=2)
            {
                bool b,s;SlotAudit(BType,BPeriod,out b,out s);
                bull=CombineAB==0 ? bull&&b : bull||b;
                bear=CombineAB==0 ? bear&&s : bear||s;
            }
            if(ConditionCount>=3)
            {
                bool b,s;SlotAudit(CType,CPeriod,out b,out s);
                bull=CombineBC==0 ? bull&&b : bull||b;
                bear=CombineBC==0 ? bear&&s : bear||s;
            }
            if(ConditionCount>=4)
            {
                bool b,s;SlotAudit(DType,DPeriod,out b,out s);
                bull=CombineCD==0 ? bull&&b : bull||b;
                bear=CombineCD==0 ? bear&&s : bear||s;
            }
            if(bull==bear)
            {
                y[yi,NoDirection]++;
                return;
            }
            y[yi,Raw]++;
            month[mi,0]++;

            // Identify ONE dominant blocking gate for this raw signal.
            // Crucially: pre-order daily submission numbers are only
            // independent predictions. See actual completed trades below.
            // V5 submits its orders BEFORE this observer runs.
            if(Position.MarketPosition!=MarketPosition.Flat)
            {
                y[yi,BlockPosition]++;
                return;
            }
            if(auditDaySubmissions>=MaxDailyEntrySubmissions)
            {
                y[yi,BlockDailyCount]++;
                return;
            }
            int stopTicks,targetTicks;
            double atr=ExitMode==0 ? 0.0 : ATR(ATRPeriod)[0];
            if(!NQNativeATRExitMathV5.TryCompute(ExitMode,atr,TickSize,
                 StopTicks,TargetTicks,ATRStopX10,ATRTargetX10,
                 out stopTicks,out targetTicks))
            {
                y[yi,BlockATR]++;
                return;
            }
            if(stopTicks*5.0 + 2.0*5.0 + 4.68>300.0)
            {
                y[yi,BlockStopBudget]++;
                return;
            }
            double closedToday=SystemPerformance.AllTrades
                .TradesPerformance.Currency.CumProfit-auditDayStartClosed;
            if(closedToday<=-600.0)
            {
                y[yi,BlockDailyLoss]++;
                return;
            }
            // Predict the same entry V5 submits on this bar.
            // Compare the prediction to actual trade counts after the run.
            y[yi,EligibleSubmit]++;
            month[mi,1]++;
            auditDaySubmissions++;
        }

        private static int NeededBarsAudit(int t,int n)
        {return t==9 ? (2*n+4) : (n+4);}

        private bool ValidGenes()
        {
            return ConditionCount>=1&&ConditionCount<=4 &&
               AType>=0&&AType<=9&&APeriod>=2&&APeriod<=117 &&
               (ConditionCount<2||(BType>=0&&BType<=9&&
                 BPeriod>=2&&BPeriod<=117&&CombineAB>=0&&CombineAB<=1)) &&
               (ConditionCount<3||(CType>=0&&CType<=9&&
                 CPeriod>=2&&CPeriod<=117&&CombineBC>=0&&CombineBC<=1)) &&
               (ConditionCount<4||(DType>=0&&DType<=9&&
                 DPeriod>=2&&DPeriod<=117&&CombineCD>=0&&CombineCD<=1)) &&
               ReverseSignals>=0&&ReverseSignals<=1 &&
               StopTicks>=1&&TargetTicks>=0 &&
               MaxDailyEntrySubmissions>=1&&MaxDailyEntrySubmissions<=2 &&
               ExitMode>=0&&ExitMode<=3&&ATRPeriod>=7&&ATRPeriod<=28 &&
               ATRStopX10>=10&&ATRStopX10<=30 &&
               ATRTargetX10>=10&&ATRTargetX10<=50 &&
               !(ExitMode==1&&TargetTicks<1);
        }

        // Independent AUDIT evaluator, identical branch predicates to V5.
        // V8 never uses this to submit, modify or cancel any order.
        private void SlotAudit(int t,int n,out bool bull,out bool bear)
        {
            bull=false;bear=false;double c,p;
            switch(t)
            {
                case 0:
                    c=SMA(Close,n)[0];p=SMA(Close,n)[1];
                    bull=c>p;bear=c<p;break;
                case 1:
                    c=EMA(Close,n)[0];p=EMA(Close,n)[1];
                    bull=c>p;bear=c<p;break;
                case 2:
                    c=WMA(Close,n)[0];p=WMA(Close,n)[1];
                    bull=c>p;bear=c<p;break;
                case 3:
                    c=RSI(Close,n,3)[0];p=RSI(Close,n,3)[1];
                    bull=c>p;bear=c<p;break;
                case 4:
                    c=CCI(Close,n)[0];p=CCI(Close,n)[1];
                    bull=c>p;bear=c<p;break;
                case 5:
                    c=SMA(Close,n)[0];
                    bull=Close[0]>c;bear=Close[0]<c;break;
                case 6:
                    c=EMA(Close,n)[0];
                    bull=Close[0]>c;bear=Close[0]<c;break;
                case 7:
                    c=RSI(Close,n,3)[0];
                    bull=c>55.0;bear=c<45.0;break;
                case 8:
                    c=CCI(Close,n)[0];
                    bull=c>100.0;bear=c< -100.0;break;
                case 9:
                    int slow=Math.Min(240,n*2);
                    c=SMA(Close,n)[0]-EMA(Close,slow)[0];
                    p=SMA(Close,n)[1]-EMA(Close,slow)[1];
                    bull=p<=0.0&&c>0.0;bear=p>=0.0&&c<0.0;
                    break;
            }
        }

        // Chronological per-bar CLOSE equity: realized plus unrealized mark
        // at the completed M1 close. This is NOT inside-minute excursion.
        // It is for one strategy/contract, not a portfolio or entire account.
        private void V8MarkEquity(int yi)
        {
            double realized=SystemPerformance.AllTrades
                .TradesPerformance.Currency.CumProfit;
            double floating=0.0;
            if(Position.MarketPosition!=MarketPosition.Flat)
                floating=Position.GetUnrealizedProfitLoss(
                    PerformanceUnit.Currency,Close[0]);
            double e=realized+floating;
            if(double.IsNaN(e)||double.IsInfinity(e))
            {
                nonFiniteEquityCount++;
                return;
            }
            if(!equityReady)
            {
                equityReady=true;
                equityPeak=Math.Max(0.0,e); // start at $0 net PnL
            }
            equityPeak=Math.Max(equityPeak,e);
            closeDDMax=Math.Max(closeDDMax,equityPeak-e);
            if(!ySeen[yi])
            {
                ySeen[yi]=true;yPeak[yi]=e;
            }
            yPeak[yi]=Math.Max(yPeak[yi],e);
            yCloseDD[yi]=Math.Max(yCloseDD[yi],yPeak[yi]-e);

            if(Time[0].Date!=markedDay)
            {
                markedDay=Time[0].Date;
                // Opening realized PnL from this bar; gaps before its
                // first observation cannot be reconstructed from M1 close.
                dailyStartEquity=realized;
                dailyPeak=realized;
                dailyReady=true;
            }
            if(dailyReady)
            {
                dailyPeak=Math.Max(dailyPeak,e);
                yDailyDD[yi]=Math.Max(yDailyDD[yi],dailyPeak-e);
                yWorstDaily[yi]=Math.Min(yWorstDaily[yi],e-dailyStartEquity);
            }
            sampledBars++;
        }

        private static string F(double v)
        {return v.ToString("F2",CultureInfo.InvariantCulture);}

        private void V8Report()
        {
            // Completed trades, grouped by entry month for comparison.
            // Do not interpret "predicted submissions" as executed fills.
            int[] tradesYear=new int[3];
            try
            {
                var hist=SystemPerformance.AllTrades;
                actualTrades=hist.Count;
                for(int i=0;i<hist.Count;i++)
                {
                    var t=hist[i];
                    if(t.Entry==null)continue;
                    DateTime dt=t.Entry.Time;
                    if(dt.Year<2020||dt.Year>2022)continue;
                    tradesYear[dt.Year-2020]++;
                    month[(dt.Year-2020)*12+dt.Month-1,2]++;
                }
            }
            catch(Exception ex)
            {
                Print("NQ_V8_AUDIT_WARNING trade_history_unavailable="+
                    ex.GetType().Name+"; signal estimates only");
            }
            string id=CanonicalRuntimeFingerprint??"";
            Print("NQ_V8_BEGIN id="+id+" observedM1="+sampledBars+
                " actualCompletedTrades="+actualTrades+
                " nonFiniteEquity="+nonFiniteEquityCount);
            for(int k=0;k<3;k++)
            {
                string s="NQ_V8_FREQ id="+id+" year="+(2020+k);
                for(int j=0;j<MetricNames.Length;j++)
                    s+=" "+MetricNames[j]+"="+y[k,j];
                s+=" actualCompletedTrades="+tradesYear[k];
                Print(s);
                Print("NQ_V8_RISK id="+id+" year="+(2020+k)+
                    " barCloseMaxDDFromYearPeak="+F(yCloseDD[k])+
                    " worstDailyFromFirstBar="+F(yWorstDaily[k])+
                    " maxDailyBarCloseDD="+F(yDailyDD[k]));
            }
            for(int m=0;m<12;m++)
            {
                int j=24+m;
                Print("NQ_V8_MONTH id="+id+" year=2022 month="+(m+1)+
                  " rawDirectional="+month[j,0]+
                  " predictedSubmissions="+month[j,1]+
                  " actualCompletedTrades="+month[j,2]);
            }
            Print("NQ_V8_END id="+id+
                " globalBarCloseMaxDD="+F(closeDDMax)+
                " actualCompletedTrades="+actualTrades+
                " predictedSubmissions="+
                  (y[0,EligibleSubmit]+y[1,EligibleSubmit]+y[2,EligibleSubmit])+
                " NOTE=RTH_M1_BAR_CLOSE_ONLY_NOT_TICKS_NOT_MFFU_TRAILING");
        }
    }
}
