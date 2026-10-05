from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

import external_strategy_replication as ext

COST_POINTS = ext.COST_POINTS
MONTHS = 60.0
YEARS = list(range(2020, 2025))
NEWS_PATH = Path("data_external/forexfactory/usd_high_medium_2020_2024.csv")


def load_news():
    n = pd.read_csv(NEWS_PATH)
    n["event_et"] = pd.to_datetime(n["event_et"], utc=True).dt.tz_convert("America/New_York")
    # Blackout is timestamp-based. Multiple FF releases at one timestamp share one window.
    times = sorted(n["event_et"].drop_duplicates().tolist())
    by_date = {}
    for t in times:
        by_date.setdefault(t.date().isoformat(), []).append(t)
    return n, by_date


def entry_in_blackout(entry_ts, events):
    for ev in events:
        if ev - pd.Timedelta(minutes=5) <= entry_ts <= ev + pd.Timedelta(minutes=5):
            return True
    return False


def first_forced_flat(entry_ts, normal_exit_ts, events):
    candidates = []
    for ev in events:
        flat = ev - pd.Timedelta(minutes=5)
        if entry_ts < flat <= normal_exit_ts:
            candidates.append(flat)
    return min(candidates) if candidates else None


def bar_close_at(g, ts):
    m = g.index[g["timestamp_et"] == ts].tolist()
    if not m:
        return None, None
    idx = int(m[0])
    return float(g.iloc[idx]["close"]), idx


def record(strategy, variant, date, direction, entry, exit_px, reason):
    gross = direction * (exit_px - entry)
    net = gross - COST_POINTS
    return {
        "strategy": strategy,
        "variant": variant,
        "date": date,
        "year": int(date[:4]),
        "direction": direction,
        "entry": entry,
        "exit": exit_px,
        "exit_reason": reason,
        "gross_points": gross,
        "net_points": net,
    }


def path_exit_news(g, start_idx, direction, entry, stop, target, entry_ts, events, eod_idx=389):
    flats = {ev - pd.Timedelta(minutes=5) for ev in events if ev - pd.Timedelta(minutes=5) > entry_ts}
    for i in range(start_idx, min(eod_idx, len(g)-1)+1):
        b = g.iloc[i]
        # Existing SL/TP can occur intrabar before the bar closes at a flat deadline.
        if direction == 1:
            if b["low"] <= stop:
                return float(stop), i, "SL"
            if b["high"] >= target:
                return float(target), i, "TP"
        else:
            if b["high"] >= stop:
                return float(stop), i, "SL"
            if b["low"] <= target:
                return float(target), i, "TP"
        if b["timestamp_et"] in flats:
            return float(b["close"]), i, "NEWS"
    i = min(eod_idx, len(g)-1)
    return float(g.iloc[i]["close"]), i, "EOD"


def or15_time_exit(sessions, news_by_date, use_news):
    rows=[]; skipped=0; forced=0
    for d,g in sessions.items():
        if len(g) < 390:
            continue
        org=g.iloc[:15]
        orh=float(org["high"].max()); orl=float(org["low"].min())
        hit=None
        for i in range(15, len(g)):
            if int(g.iloc[i]["minute"]) > 690:  # 11:30 EOB label
                break
            c=float(g.iloc[i]["close"])
            if c > orh:
                hit=(i,1); break
            if c < orl:
                hit=(i,-1); break
        if hit is None:
            continue
        i,direction=hit
        entry_idx=i+1
        exit_idx=i+30
        if exit_idx >= len(g):
            continue
        entry=float(g.iloc[entry_idx]["open"])
        entry_ts=g.iloc[i]["timestamp_et"]  # next bar opens at signal close timestamp
        normal_exit_ts=g.iloc[exit_idx]["timestamp_et"]
        events=news_by_date.get(d,[])
        if use_news and entry_in_blackout(entry_ts,events):
            skipped += 1
            continue
        exit_px=float(g.iloc[exit_idx]["close"]); reason="TIME30"
        if use_news:
            flat=first_forced_flat(entry_ts,normal_exit_ts,events)
            if flat is not None:
                px,_=bar_close_at(g,flat)
                if px is not None:
                    exit_px=px; reason="NEWS"; forced += 1
        rows.append(record("OR15 first breakout 30m", "NEWS" if use_news else "BASE", d,
                           direction, entry, exit_px, reason))
    return rows,skipped,forced


def overnight_reversal(sessions, news_by_date, use_news):
    rows=[]; skipped=0; forced=0; dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]; pg=sessions[prev]
        prev_close=float(pg.iloc[-1]["close"])
        entry=float(g.iloc[0]["open"])
        ov=entry/prev_close-1
        if ov==0: continue
        direction=-1 if ov>0 else 1
        entry_ts=g.iloc[0]["timestamp_et"]-pd.Timedelta(minutes=1)
        normal_idx=29
        normal_exit_ts=g.iloc[normal_idx]["timestamp_et"]
        events=news_by_date.get(d,[])
        if use_news and entry_in_blackout(entry_ts,events):
            skipped += 1; continue
        exit_px=float(g.iloc[normal_idx]["close"]); reason="TIME"
        if use_news:
            flat=first_forced_flat(entry_ts,normal_exit_ts,events)
            if flat is not None:
                px,_=bar_close_at(g,flat)
                if px is not None:
                    exit_px=px; reason="NEWS"; forced += 1
        rows.append(record("Academic overnight reversal 09:30-10:00",
                           "NEWS" if use_news else "BASE",d,direction,entry,exit_px,reason))
    return rows,skipped,forced


def intraday_momentum(sessions, news_by_date, use_news):
    rows=[]; skipped=0; forced=0; dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]; pg=sessions[prev]
        prev_close=float(pg.iloc[-1]["close"])
        sig=float(g.iloc[29]["close"])/prev_close-1
        if sig==0: continue
        direction=1 if sig>0 else -1
        entry_idx=360
        entry=float(g.iloc[entry_idx]["open"])
        entry_ts=g.iloc[entry_idx]["timestamp_et"]-pd.Timedelta(minutes=1)
        normal_exit_ts=g.iloc[-1]["timestamp_et"]
        events=news_by_date.get(d,[])
        if use_news and entry_in_blackout(entry_ts,events):
            skipped += 1; continue
        exit_px=float(g.iloc[-1]["close"]); reason="TIME"
        if use_news:
            flat=first_forced_flat(entry_ts,normal_exit_ts,events)
            if flat is not None:
                px,_=bar_close_at(g,flat)
                if px is not None:
                    exit_px=px; reason="NEWS"; forced += 1
        rows.append(record("Academic intraday momentum 15:30-16:00",
                           "NEWS" if use_news else "BASE",d,direction,entry,exit_px,reason))
    return rows,skipped,forced


def public_orb15(sessions, news_by_date, use_news):
    rows=[]; skipped=0; forced=0
    for d,g in sessions.items():
        org=g.iloc[:15]
        orh=float(org["high"].max()); orl=float(org["low"].min())
        chosen=None
        for group in range(1,10):
            s=group*15; e=s+15
            if e>len(g): break
            candle=g.iloc[s:e]
            c=float(candle.iloc[-1]["close"])
            direction=1 if c>orh else (-1 if c<orl else 0)
            if direction==0: continue
            entry_idx=e
            if entry_idx>=len(g): break
            entry_clock=570+entry_idx
            if entry_clock>=720: break
            chosen=(direction,entry_idx); break
        if chosen is None: continue
        direction,entry_idx=chosen
        entry=float(g.iloc[entry_idx]["open"])
        entry_ts=g.iloc[entry_idx]["timestamp_et"]-pd.Timedelta(minutes=1)
        stop=orl if direction==1 else orh
        risk=abs(entry-stop)
        if risk<=0: continue
        target=entry+direction*1.5*risk
        events=news_by_date.get(d,[])
        if use_news and entry_in_blackout(entry_ts,events):
            skipped += 1; continue
        if use_news:
            exit_px,_,reason=path_exit_news(g,entry_idx,direction,entry,stop,target,entry_ts,events,389)
            if reason=="NEWS": forced += 1
        else:
            exit_px,_,reason=ext.path_exit(g,entry_idx,direction,entry,stop,target,389)
        rows.append(record("Public ORB15 SL=opposite edge TP=1.5R",
                           "NEWS" if use_news else "BASE",d,direction,entry,exit_px,reason))
    return rows,skipped,forced


def return_to_value(sessions, news_by_date, use_news):
    rows=[]; skipped=0; forced=0; dates=sorted(sessions)
    levels={d:ext.tpo_value_area(g) for d,g in sessions.items()}
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]
        _,vah,val=levels[prev]
        if not np.isfinite(vah): continue
        op=float(g.iloc[0]["open"])
        first=g.iloc[:30]; second=g.iloc[30:60]
        close2=float(second.iloc[-1]["close"])
        direction=0; edge=None; target=None
        if op>vah and float(first["low"].min())>vah and val<=close2<=vah:
            direction=-1; edge=vah; target=val
        elif op<val and float(first["high"].max())<val and val<=close2<=vah:
            direction=1; edge=val; target=vah
        if direction==0: continue
        entry_idx=60
        entry=float(g.iloc[entry_idx]["open"])
        entry_ts=g.iloc[entry_idx]["timestamp_et"]-pd.Timedelta(minutes=1)
        stop=edge+(1.5 if direction==-1 else -1.5)
        if direction==1 and not (stop<entry<target): continue
        if direction==-1 and not (target<entry<stop): continue
        events=news_by_date.get(d,[])
        if use_news and entry_in_blackout(entry_ts,events):
            skipped += 1; continue
        if use_news:
            exit_px,_,reason=path_exit_news(g,entry_idx,direction,entry,stop,target,entry_ts,events,389)
            if reason=="NEWS": forced += 1
        else:
            exit_px,_,reason=ext.path_exit(g,entry_idx,direction,entry,stop,target,389)
        rows.append(record("Market Profile return-to-value 6tick stop",
                           "NEWS" if use_news else "BASE",d,direction,entry,exit_px,reason))
    return rows,skipped,forced


def metrics(df):
    if df.empty:
        return {}
    pos=df.loc[df.net_points>0,"net_points"].sum()
    neg=-df.loc[df.net_points<0,"net_points"].sum()
    pf=pos/neg if neg>0 else np.inf
    yearly=df.groupby("year")["net_points"].sum().reindex(YEARS,fill_value=0.0)
    return {
        "trades":len(df),
        "trades_per_month":len(df)/MONTHS,
        "net_points_per_trade":df.net_points.mean(),
        "net_profit_factor":pf,
        "win_rate":(df.net_points>0).mean(),
        "total_net_points":df.net_points.sum(),
        "positive_years":int((yearly>0).sum()),
        "yearly_net":"; ".join(f"{y}:{yearly.loc[y]:.2f}" for y in YEARS),
    }


def main():
    if not NEWS_PATH.exists():
        raise RuntimeError(f"Missing news calendar: {NEWS_PATH}")
    news,news_by_date=load_news()
    print("Scheduled USD High/Medium rows:",len(news),"unique timestamps:",news["event_et"].nunique())

    x=ext.stitch_mes()
    sessions=ext.rth_sessions(x)
    print("Full RTH sessions:",len(sessions))

    tests=[
        or15_time_exit,
        overnight_reversal,
        intraday_momentum,
        public_orb15,
        return_to_value,
    ]
    allrows=[]; summaries=[]
    for fn in tests:
        base,_,_=fn(sessions,news_by_date,False)
        filt,skipped,forced=fn(sessions,news_by_date,True)
        allrows.extend(base); allrows.extend(filt)
        bdf=pd.DataFrame(base); fdf=pd.DataFrame(filt)
        name=(bdf.strategy.iloc[0] if len(bdf) else (fdf.strategy.iloc[0] if len(fdf) else fn.__name__))
        bm=metrics(bdf); fm=metrics(fdf)
        summaries.append({
            "strategy":name,
            "base_trades":bm.get("trades",0),
            "news_trades":fm.get("trades",0),
            "entry_skipped":skipped,
            "forced_news_exits":forced,
            "base_net_pts_trade":bm.get("net_points_per_trade",np.nan),
            "news_net_pts_trade":fm.get("net_points_per_trade",np.nan),
            "delta_net_pts_trade":fm.get("net_points_per_trade",np.nan)-bm.get("net_points_per_trade",np.nan),
            "base_pf":bm.get("net_profit_factor",np.nan),
            "news_pf":fm.get("net_profit_factor",np.nan),
            "delta_pf":fm.get("net_profit_factor",np.nan)-bm.get("net_profit_factor",np.nan),
            "base_win_rate":bm.get("win_rate",np.nan),
            "news_win_rate":fm.get("win_rate",np.nan),
            "base_total_net":bm.get("total_net_points",np.nan),
            "news_total_net":fm.get("total_net_points",np.nan),
            "base_positive_years":bm.get("positive_years",0),
            "news_positive_years":fm.get("positive_years",0),
            "base_yearly":bm.get("yearly_net",""),
            "news_yearly":fm.get("yearly_net",""),
        })

    trades=pd.DataFrame(allrows)
    summary=pd.DataFrame(summaries)

    # News exposure during the user's preferred morning research window.
    n=news.copy()
    n["hourmin"]=n["event_et"].dt.hour*60+n["event_et"].dt.minute
    morning=n[(n["hourmin"]>=570)&(n["hourmin"]<=690)]
    exposure=pd.DataFrame([{
        "calendar_rows_total":len(n),
        "unique_event_timestamps_total":n["event_et"].nunique(),
        "morning_rows_0930_1130":len(morning),
        "morning_unique_timestamps_0930_1130":morning["event_et"].nunique(),
        "morning_high_rows":int((morning["impact"]=="High").sum()),
        "morning_medium_rows":int((morning["impact"]=="Medium").sum()),
    }])

    out=Path("results/news_filter_retest")
    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/"trades.csv",index=False)
    summary.to_csv(out/"summary.csv",index=False)
    exposure.to_csv(out/"calendar_exposure.csv",index=False)

    print("\n=== FOREX FACTORY NEWS FILTER RETEST ===")
    cols=["strategy","base_trades","news_trades","entry_skipped","forced_news_exits",
          "base_net_pts_trade","news_net_pts_trade","delta_net_pts_trade",
          "base_pf","news_pf","delta_pf","base_positive_years","news_positive_years"]
    print(summary[cols].round(4).to_string(index=False))
    print("\n=== YEARLY ===")
    for _,r in summary.iterrows():
        print(r["strategy"])
        print(" BASE",r["base_yearly"])
        print(" NEWS",r["news_yearly"])
    print("\n=== CALENDAR EXPOSURE ===")
    print(exposure.to_string(index=False))

if __name__=="__main__":
    main()

# PR trigger only; frozen news rules unchanged
