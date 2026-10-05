from __future__ import annotations

from pathlib import Path
import math
import numpy as np
import pandas as pd

import external_strategy_replication as ext

COST_POINTS = ext.COST_POINTS
TICK = 0.25
MONTHS = 60.0
YEARS = list(range(2020, 2025))
ENTRY_START = 9*60 + 30
ENTRY_END = 11*60 + 30
NEWS_PATH = Path("data_external/forexfactory/usd_high_medium_2020_2024.csv")


def load_news():
    n=pd.read_csv(NEWS_PATH)
    n["event_et"]=pd.to_datetime(n["event_et"],utc=True).dt.tz_convert("America/New_York")
    by={}
    for t in sorted(n["event_et"].drop_duplicates()):
        by.setdefault(t.date().isoformat(),[]).append(t)
    return by


def in_blackout(ts, events):
    return any(ev-pd.Timedelta(minutes=5) <= ts <= ev+pd.Timedelta(minutes=5) for ev in events)


def news_deadlines(events, after, through):
    return sorted(ev-pd.Timedelta(minutes=5) for ev in events
                  if after < ev-pd.Timedelta(minutes=5) <= through)


def record(name,date,direction,entry,exit_px,reason):
    gross=direction*(exit_px-entry)
    net=gross-COST_POINTS
    return dict(strategy=name,date=date,year=int(date[:4]),direction=direction,
                entry=entry,exit=exit_px,exit_reason=reason,
                gross_points=gross,net_points=net,net_dollars=net*5.0)


def wilder_rsi(s, period=14):
    arr=s.to_numpy(dtype=float)
    out=np.full(len(arr),np.nan)
    if len(arr)<=period: return pd.Series(out,index=s.index)
    d=np.diff(arr,prepend=np.nan)
    gain=np.where(d>0,d,0.0)
    loss=np.where(d<0,-d,0.0)
    avg_g=np.nanmean(gain[1:period+1])
    avg_l=np.nanmean(loss[1:period+1])
    def val(g,l):
        if l==0: return 100.0 if g>0 else 50.0
        rs=g/l
        return 100-100/(1+rs)
    out[period]=val(avg_g,avg_l)
    for i in range(period+1,len(arr)):
        avg_g=(avg_g*(period-1)+gain[i])/period
        avg_l=(avg_l*(period-1)+loss[i])/period
        out[i]=val(avg_g,avg_l)
    return pd.Series(out,index=s.index)


def enrich_sessions(sessions):
    z=[]
    for d,g in sessions.items():
        q=g.copy(); q["_datekey"]=d; q["_row"]=range(len(q)); z.append(q)
    x=pd.concat(z,ignore_index=True).sort_values("timestamp_et").reset_index(drop=True)
    x["ema5"]=x["close"].ewm(span=5,adjust=False).mean()
    x["ema34"]=x["close"].ewm(span=34,adjust=False).mean()
    up=(x["ema5"]>x["ema34"])&(x["ema5"].shift(1)<=x["ema34"].shift(1))
    dn=(x["ema5"]<x["ema34"])&(x["ema5"].shift(1)>=x["ema34"].shift(1))
    x["ema_cross_up_3"]=up.astype(int).rolling(3,min_periods=1).max().astype(bool)
    x["ema_cross_dn_3"]=dn.astype(int).rolling(3,min_periods=1).max().astype(bool)
    x["rsi14"]=wilder_rsi(x["close"],14)
    x["rsi_cross20"]=(x["rsi14"]>20)&(x["rsi14"].shift(1)<=20)
    return {d:g.reset_index(drop=True) for d,g in x.groupby("_datekey",sort=True)}


def common_path_exit(g,start_idx,direction,entry,stop,target,entry_ts,events,eod_idx=389):
    deadlines=set(news_deadlines(events,entry_ts,g.iloc[eod_idx]["timestamp_et"]))
    # NinjaTrader bars are EOB labeled. A forced flat at T-5 uses the OPEN
    # of the bar starting at T-5, whose label is T-5 + 1 minute.
    deadline_labels={d+pd.Timedelta(minutes=1) for d in deadlines}
    for i in range(start_idx,eod_idx+1):
        b=g.iloc[i]
        if b["timestamp_et"] in deadline_labels:
            return float(b["open"]),i,"NEWS"
        if direction==1:
            if stop is not None and b["low"]<=stop:
                fill=min(stop,float(b["open"])) if float(b["open"])<stop else stop
                return float(fill),i,"SL"
            if target is not None and b["high"]>=target:
                fill=max(target,float(b["open"])) if float(b["open"])>target else target
                return float(fill),i,"TP"
        else:
            if stop is not None and b["high"]>=stop:
                fill=max(stop,float(b["open"])) if float(b["open"])>stop else stop
                return float(fill),i,"SL"
            if target is not None and b["low"]<=target:
                fill=min(target,float(b["open"])) if float(b["open"])<target else target
                return float(fill),i,"TP"
    return float(g.iloc[eod_idx]["close"]),eod_idx,"EOD"


def simulate_barclose_strategy(sessions,news_by_date,name,kind):
    rows=[]; skipped_news=0; ambiguous=0
    for d,g in sessions.items():
        events=news_by_date.get(d,[])
        available_idx=0
        for i in range(max(35,available_idx),len(g)-1):
            if i<available_idx: continue
            signal_ts=g.iloc[i]["timestamp_et"]
            entry_ts=signal_ts  # next 1m bar opens at this EOB timestamp
            hm=entry_ts.hour*60+entry_ts.minute
            if hm<ENTRY_START or hm>ENTRY_END: continue
            direction=0; stop=None; target=None
            entry=float(g.iloc[i+1]["open"])

            if kind=="ema":
                up=bool(g.iloc[i]["ema_cross_up_3"]); dn=bool(g.iloc[i]["ema_cross_dn_3"])
                if up and dn:
                    ambiguous+=1; continue
                if up: direction=1
                elif dn: direction=-1
                else: continue
                stop=entry-direction*15*TICK
                target=entry+direction*20*TICK

            elif kind=="rsi":
                if not bool(g.iloc[i]["rsi_cross20"]): continue
                direction=1
                stop=entry-6*TICK
                target=entry+12*TICK

            elif kind=="doji":
                b=g.iloc[i]
                if float(b["open"])!=float(b["close"]): continue
                rng=float(b["high"]-b["low"])
                if rng<=0: continue
                direction=1
                stop=float(b["low"])-2*TICK
                target=entry+rng
                if entry<=stop: continue
            else:
                raise ValueError(kind)

            if in_blackout(entry_ts,events):
                skipped_news+=1
                continue
            exit_px,exit_idx,reason=common_path_exit(
                g,i+1,direction,entry,stop,target,entry_ts,events,389)
            rows.append(record(name,d,direction,entry,exit_px,reason))
            available_idx=exit_idx
    return rows,skipped_news,ambiguous


def aggregate_30m(g):
    bars=[]
    for j in range(13):
        b=g.iloc[j*30:(j+1)*30]
        if len(b)<30: break
        bars.append(dict(block=j,start_idx=j*30,end_idx=(j+1)*30-1,
                         open=float(b.iloc[0]["open"]),high=float(b["high"].max()),
                         low=float(b["low"].min()),close=float(b.iloc[-1]["close"]),
                         close_ts=b.iloc[-1]["timestamp_et"]))
    return pd.DataFrame(bars)


def channel5_es30(sessions,news_by_date):
    name="NT-F04 ES30m 5-bar channel long"
    rows=[]; skipped_news=0
    for d,g in sessions.items():
        b30=aggregate_30m(g)
        events=news_by_date.get(d,[])
        j=4
        while j < len(b30)-1:
            entry_level=float(b30.loc[j-4:j,"high"].max())
            next_start=int(b30.loc[j+1,"start_idx"]); next_end=int(b30.loc[j+1,"end_idx"])
            entered=None
            for k in range(next_start,next_end+1):
                bar=g.iloc[k]
                ts=bar["timestamp_et"]
                hm=(ts-pd.Timedelta(minutes=1)).hour*60+(ts-pd.Timedelta(minutes=1)).minute
                if hm>ENTRY_END: break
                if hm<ENTRY_START: continue
                if bar["high"]>=entry_level:
                    actual_ts=ts-pd.Timedelta(minutes=1)
                    if in_blackout(actual_ts,events):
                        skipped_news+=1
                        continue
                    fill=max(entry_level,float(bar["open"]))
                    entered=(k,fill,actual_ts)
                    break
            if entered is None:
                j+=1; continue
            entry_idx,entry,entry_ts=entered

            # No channel exit order is known until the entry 30m bar closes.
            entry_block=int(entry_idx//30)
            normal_exit=None
            news_dl=news_deadlines(events,entry_ts,g.iloc[-1]["timestamp_et"])
            # News can flatten even within entry block.
            for k in range(entry_idx, int(b30.loc[entry_block,"end_idx"])+1):
                if g.iloc[k]["timestamp_et"] in {d+pd.Timedelta(minutes=1) for d in news_dl}:
                    normal_exit=(float(g.iloc[k]["open"]),k,"NEWS"); break
            if normal_exit is None:
                q=entry_block
                while q < len(b30)-1 and normal_exit is None:
                    exit_level=float(b30.loc[max(0,q-4):q,"low"].min())
                    s=int(b30.loc[q+1,"start_idx"]); e=int(b30.loc[q+1,"end_idx"])
                    deadlines={d+pd.Timedelta(minutes=1) for d in news_deadlines(events,entry_ts,g.iloc[e]["timestamp_et"])}
                    for k in range(s,e+1):
                        bar=g.iloc[k]
                        if bar["low"]<=exit_level:
                            fill=min(exit_level,float(bar["open"]))
                            normal_exit=(fill,k,"CHANNEL"); break
                        if bar["timestamp_et"] in deadlines:
                            normal_exit=(float(bar["open"]),k,"NEWS"); break
                    q+=1
            if normal_exit is None:
                normal_exit=(float(g.iloc[-1]["close"]),389,"EOD")
            exit_px,exit_idx,reason=normal_exit
            rows.append(record(name,d,1,entry,exit_px,reason))
            j=max(j+1,int(exit_idx//30))
    return rows,skipped_news,0


def range_breakout_0930_1030(full, sessions, news_by_date):
    name="NT-F05 09:30-10:30 range breakout"
    rows=[]; skipped_news=0; ambiguous=0
    by_date={d:g.sort_values("timestamp_et").reset_index(drop=True)
             for d,g in full.groupby("date",sort=True)}
    for d,rth in sessions.items():
        if d not in by_date: continue
        # first 60 RTH one-minute bars: 09:30-10:30 actual, labels 09:31..10:30
        opening=rth.iloc[:60]
        if len(opening)<60: continue
        hi=float(opening["high"].max()); lo=float(opening["low"].min())
        long_level=hi+TICK; short_level=lo-TICK
        long_stop=lo-TICK; short_stop=hi+TICK
        day=by_date[d]
        # after range close through user's last allowed entry 11:30
        cand=day[(day["minute"]>=631)&(day["minute"]<=690)].copy()
        events=news_by_date.get(d,[])
        entry=None
        for _,bar in cand.iterrows():
            hit_l=float(bar["high"])>=long_level
            hit_s=float(bar["low"])<=short_level
            if hit_l and hit_s:
                ambiguous+=1; entry=None; break
            if not hit_l and not hit_s: continue
            direction=1 if hit_l else -1
            level=long_level if direction==1 else short_level
            # approximate intraminute entry time by bar start
            entry_ts=bar["timestamp_et"]-pd.Timedelta(minutes=1)
            if in_blackout(entry_ts,events):
                skipped_news+=1
                continue
            fill=(max(level,float(bar["open"])) if direction==1
                  else min(level,float(bar["open"])))
            entry=(direction,fill,entry_ts,bar["timestamp_et"])
            break
        if entry is None: continue
        direction,fill,entry_ts,entry_bar_label=entry
        stop=long_stop if direction==1 else short_stop
        # scan from entry bar through 18:00 EOB label
        scan=day[(day["timestamp_et"]>=entry_bar_label)&(day["minute"]<=1080)]
        deadlines={d+pd.Timedelta(minutes=1) for d in news_deadlines(events,entry_ts,
                         scan.iloc[-1]["timestamp_et"] if len(scan) else entry_bar_label)}
        exit_px=None; reason=None
        for _,bar in scan.iterrows():
            if direction==1 and float(bar["low"])<=stop:
                exit_px=min(stop,float(bar["open"])); reason="SL"; break
            if direction==-1 and float(bar["high"])>=stop:
                exit_px=max(stop,float(bar["open"])); reason="SL"; break
            if bar["timestamp_et"] in deadlines:
                exit_px=float(bar["open"]); reason="NEWS"; break
        if exit_px is None:
            if len(scan):
                exit_px=float(scan.iloc[-1]["close"]); reason="TIME18"
            else:
                continue
        rows.append(record(name,d,direction,fill,exit_px,reason))
    return rows,skipped_news,ambiguous


def metrics(df):
    if df.empty: return {}
    pos=df.loc[df.net_points>0,"net_points"].sum()
    neg=-df.loc[df.net_points<0,"net_points"].sum()
    pf=pos/neg if neg>0 else np.inf
    yearly=df.groupby("year")["net_points"].sum().reindex(YEARS,fill_value=0.0)
    pos_year=yearly.clip(lower=0)
    max_share=float(pos_year.max()/pos_year.sum()) if pos_year.sum()>0 else np.nan
    return dict(trades=len(df),trades_per_month=len(df)/MONTHS,
                net_pts_trade=df.net_points.mean(),pf_net=pf,
                win_rate=(df.net_points>0).mean(),total_net=df.net_points.sum(),
                positive_years=int((yearly>0).sum()),max_positive_year_share=max_share,
                yearly="; ".join(f"{y}:{yearly.loc[y]:.2f}" for y in YEARS))


def main():
    news=load_news()
    full=ext.stitch_mes()
    sessions=ext.rth_sessions(full)
    sessions=enrich_sessions(sessions)
    print("RTH sessions:",len(sessions))

    results=[]
    meta=[]

    r,skip,amb=simulate_barclose_strategy(
        sessions,news,"NT-F01 EMA5/34 cross TP20 SL15","ema")
    results+=r; meta.append(("NT-F01 EMA5/34 cross TP20 SL15",skip,amb,"forum adaptation MES1m"))

    r,skip,amb=simulate_barclose_strategy(
        sessions,news,"NT-F02 NinjaTrader RSI14 cross20 TP12 SL6","rsi")
    results+=r; meta.append(("NT-F02 NinjaTrader RSI14 cross20 TP12 SL6",skip,amb,"official NT adaptation MES1m"))

    r,skip,amb=simulate_barclose_strategy(
        sessions,news,"NT-F03 exact-doji long dynamic target","doji")
    results+=r; meta.append(("NT-F03 exact-doji long dynamic target",skip,amb,"forum adaptation MES1m"))

    r,skip,amb=channel5_es30(sessions,news)
    results+=r; meta.append(("NT-F04 ES30m 5-bar channel long",skip,amb,"forum ES30m replication on MES"))

    r,skip,amb=range_breakout_0930_1030(full,sessions,news)
    results+=r; meta.append(("NT-F05 09:30-10:30 range breakout",skip,amb,"forum range-breakout replication"))

    trades=pd.DataFrame(results)
    summary=[]
    for name,skip,amb,fidelity in meta:
        g=trades[trades.strategy==name].copy() if len(trades) else pd.DataFrame()
        m=metrics(g)
        gate={
            "gate_net_positive":bool(m and m["net_pts_trade"]>0),
            "gate_pf_125":bool(m and m["pf_net"]>=1.25),
            "gate_5_per_month":bool(m and m["trades"]>=300),
            "gate_4_of_5_years":bool(m and m["positive_years"]>=4),
            "gate_year_concentration":bool(m and np.isfinite(m["max_positive_year_share"]) and m["max_positive_year_share"]<=0.40),
        }
        summary.append(dict(strategy=name,source_fidelity=fidelity,
                            news_entry_skips=skip,ambiguous_skips=amb,**m,**gate,
                            passes_primary_gate=all(gate.values())))
    summary=pd.DataFrame(summary)

    out=Path("results/ninjatrader_community_challenge")
    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/"trades.csv",index=False)
    summary.to_csv(out/"summary.csv",index=False)

    print("\n=== NINJATRADER COMMUNITY STRATEGY CHALLENGE ===")
    cols=["strategy","trades","trades_per_month","net_pts_trade","pf_net","win_rate",
          "total_net","positive_years","max_positive_year_share","news_entry_skips",
          "ambiguous_skips","passes_primary_gate"]
    print(summary[cols].round(4).to_string(index=False))
    print("\n=== YEARLY ===")
    for _,r in summary.iterrows():
        print(r["strategy"],"::",r.get("yearly",""))
    print("\nPASSED:",summary.loc[summary.passes_primary_gate,"strategy"].tolist())

if __name__=="__main__":
    main()

# PR trigger only; corrected T-5 news exit logic unchanged
