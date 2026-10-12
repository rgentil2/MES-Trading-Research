#!/usr/bin/env python3
"""NQ B05H: causal transaction-count bars with whole-timestamp atomic groups.

NO five-second bars, NO alpha, NO trading/fills, NO historical-data requests.
This module validates synthetic/user-provided DEV Last iterables and produces
completed bars by minimum PRINT count, NOT exact N prints when a tied-timestamp
group crosses the boundary. VWAP is integer ratio, permutation-invariant.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import groupby
from typing import Iterable, Iterator

from qc_tick_day import utc_bounds
from nq_tick_short_horizon import dev_day

LENGTHS = (233,377,4181,10946)

@dataclass(frozen=True)
class CompletedPrintBar:
    min_print_threshold: int
    prints: int
    total_qty: int
    price_times_qty_ticks: int
    high_ticks: int
    low_ticks: int
    start_timestamp: int
    end_timestamp: int
    whole_timestamp_groups: int

    @property
    def overshoot_prints(self) -> int:
        return self.prints-self.min_print_threshold

    @property
    def vwap_numerator(self) -> int:
        return self.price_times_qty_ticks

    @property
    def vwap_denominator(self) -> int:
        return self.total_qty

    # Never use the last arbitrary trade as a bar close or as an executable fill.

@dataclass
class _Builder:
    threshold: int
    def __post_init__(self):
        if type(self.threshold) is not int or self.threshold < 1:
            raise ValueError("bad positive print threshold")
        self.reset()
    def reset(self):
        self.prints=0
        self.total_qty=0
        self.pxqty=0
        self.hi=None
        self.lo=None
        self.first=None
        self.last=None
        self.groups=0
    def add_group(self,ts,rows):
        if not rows: raise ValueError('empty timestamp group')
        if self.first is None:self.first=ts
        self.last=ts
        self.groups+=1
        for _,px,qty in rows:
            self.prints+=1
            self.total_qty+=qty
            self.pxqty+=px*qty
            self.hi=px if self.hi is None else max(self.hi,px)
            self.lo=px if self.lo is None else min(self.lo,px)
        if self.prints < self.threshold:return None
        result=CompletedPrintBar(
            self.threshold,self.prints,self.total_qty,self.pxqty,
            self.hi,self.lo,self.first,self.last,self.groups)
        if result.overshoot_prints < 0: raise AssertionError("bad threshold close")
        self.reset()
        return result

def completed_bars_by_print_count(
    events: Iterable[tuple[int,int,int]],
    day: str,
    lengths: tuple[int,...]=LENGTHS,
) -> dict[int,list[CompletedPrintBar]]:
    """Complete groups then close by print-count thresholds, no fixed-time bars.

    Input must be Last (utc100ns, price in 0.25-NQ-price ticks, positive qty).
    The DEV day is rejected *before* iterating events. The result is NOT
    a synthetic trade signal, broker execution or a claim of exchange sequence.
    """
    d=dev_day(day)  # no sealed event read
    lo,hi=utc_bounds(d)
    if (not lengths or len(set(lengths))!=len(lengths)
            or any(type(n) is not int or n<1 for n in lengths)):
        raise ValueError('invalid unique positive print thresholds')
    constructors={n:_Builder(n) for n in lengths}
    complete={n:[] for n in lengths}
    previous=None
    for ts,rows_it in groupby(events,key=lambda e:e[0]):
        rows=list(rows_it)  # no mid-timestamp decision
        if type(ts) is not int or not lo <= ts < hi:
            raise ValueError('B05H Timestamp outside DEV 08:00..12:00 ET')
        if previous is not None and ts<=previous:
            raise ValueError('B05H Unsorted timestamp groups')
        for row in rows:
            if (not isinstance(row,tuple) or len(row)!=3
                    or row[0]!=ts or type(row[1]) is not int
                    or row[1]<=0 or type(row[2]) is not int
                    or row[2]<=0):
                raise ValueError('B05H Bad price, qty, timestamp or source schema')
        for n,b in constructors.items():
            finished=b.add_group(ts,rows)
            if finished is not None:
                complete[n].append(finished)
        previous=ts
    return complete

def prior_completed_context(bar_series:list[CompletedPrintBar], timestamp:int,
                            min_number:int=2) -> list[CompletedPrintBar] | None:
    """Context strictly prior to the decision timestamp.

    Equal-time group must not be used as an already-known external context.
    For a signal on a just-completed small bar, use previous context bars
    whose *end_timestamp is strictly smaller*.
    """
    if type(timestamp) is not int or min_number<1: raise ValueError("bad context")
    completed=[b for b in bar_series if b.end_timestamp<timestamp]
    return completed[-min_number:] if len(completed)>=min_number else None
