#!/usr/bin/env python3
"""V2.6 NQ 132-block structural population, not a strategy backtest.

Includes both random combination and genetic recombination. The original
V2.1 38-block campaign remains SHA-frozen; V2.6 has its own AST_VERSION,
seed, SHA lineage and explicit typed threshold operations. All 132 names are
mathematically routable, but NOT all independently certified. No PnL/ranking,
no market/ISV/holdout access, no synthetic winning-strategy claims.
"""
from __future__ import annotations
import copy
import hashlib
import json
import random
from research.nq.nq_m1_v2_generator import (
 read_registry,sample_parameters,sample_exit,ENTRY_TYPES,IST,
 permitted_years_for_generation
)
from research.nq.nq_m1_v26_all_132_router import inventory,PREDICATE_FIELDS

VERSION="NQ_M1_V26_132_TECHNICAL_CANDIDATE_AST_UNCERTIFIED"
STATUS="STRUCTURAL_ONLY_NEEDS_13_GATES_NO_MARKET_NO_PNL"
SEED=20261028
LEVEL_OPS=("ABOVE_LEVEL","BELOW_LEVEL","CROSS_ABOVE_LEVEL","CROSS_BELOW_LEVEL")
LAG_OPS=("RISING","FALLING","ABOVE_LAG","BELOW_LAG","CROSSES_OWN_LAG")
OUTPUTS={
 "Bollinger Bands":("upper","lower","middle","width"),
 "Keltner":("upper","lower","middle","width"),
 "Acceleration Bands":("upper","lower","middle","width"),
 "Central Pivot Range":("upper","lower","middle"),
 "Classic Pivots":("upper","lower","middle"),
 "Fibonacci Pivots":("upper","lower","middle"),
 "Camarilla Pivots":("upper","lower","middle"),
 "Woodie Pivots":("upper","lower","middle"),
 "DeMark Pivots":("upper","lower","middle"),
 "Previous Day High/Low":("upper","lower","middle","width"),
 "RSI":("lower_level","upper_level")
}

def block(rng,entry):
    vals=sample_parameters(rng,entry["parameters"])
    result={"registry_id":entry["id"],"name":entry["name"],"parameters":vals}
    if entry["name"] in OUTPUTS:
        result["output"]=rng.choice(OUTPUTS[entry["name"]])
    return result

def leaf(rng,entry):
    chosen=block(rng,entry)
    thresholded=bool(set(chosen["parameters"])&PREDICATE_FIELDS)
    if thresholded:
        op=rng.choice(LEVEL_OPS)
        # Router has already converted catalogue threshold into signed zero
        # crossing. This level is a genuine causal comparison, not inert AST.
        return {"indicator":chosen,"op":op,"threshold":0.0}
    op=rng.choice(LAG_OPS)
    return {"indicator":chosen,"op":op,"lag_completed_bars":rng.randint(1,20)}

def tree(rng,entries,max_conditions):
    if not 1<=max_conditions<=100:raise ValueError("Max conditions 1..100")
    exprs=[leaf(rng,rng.choice(entries)) for _ in range(rng.randint(1,max_conditions))]
    while len(exprs)>1:
        left=exprs.pop(rng.randrange(len(exprs)))
        right=exprs.pop(rng.randrange(len(exprs)))
        exprs.append({"op":rng.choice(("AND","OR")),"left":left,"right":right})
    return exprs[0]

def strategy(rng,entries,max_conditions=8):
    typ=rng.choice(ENTRY_TYPES)
    return {
        "schema":"NQ_M1_V26_AST_PRE_ECONOMIC",
        "ast_version":VERSION,"universe":"NQ_M1",
        "position_sizing":{"instrument":"NQ","contracts":1},
        "signal_clock":"America/New_York","bars_are_end_labeled":True,
        "signal_uses_completed_bars_only":True,
        "market_data_years_permitted_for_discovery":list(IST),
        "long":tree(rng,entries,max_conditions),
        "short":tree(rng,entries,max_conditions),
        "entry_order":{"kind":typ,"offset_ticks":rng.randint(0,32) if typ!="MARKET" else 0,
                       "expiry_bars":rng.randint(1,30) if typ!="MARKET" else 1},
        "exit":sample_exit(rng)
    }

def canonical(s):
    # No PnL can enter fingerprint. Identity and parent IDs are excluded.
    immutable={k:v for k,v in s.items() if k not in ("id","lineage")}
    return json.dumps(immutable,sort_keys=True,separators=(",",":"))

def sha(s):
    return hashlib.sha256(canonical(s).encode()).hexdigest()

def mutate(rng,parent,entries,max_conditions=8):
    s=copy.deepcopy({k:v for k,v in parent.items() if k not in ("id","lineage")})
    choice=rng.choice(("long","short","entry_order","exit"))
    if choice in ("long","short"):
        s[choice]=tree(rng,entries,max_conditions)
    elif choice=="exit":
        s["exit"]=sample_exit(rng)
    else:
        kind=rng.choice(ENTRY_TYPES)
        s["entry_order"]={"kind":kind,"offset_ticks":rng.randint(0,32) if kind!="MARKET" else 0,
                          "expiry_bars":rng.randint(1,30) if kind!="MARKET" else 1}
    return s

def crossover(rng,a,b):
    s=copy.deepcopy({k:v for k,v in a.items() if k not in ("id","lineage")})
    for k in rng.sample(("long","short","entry_order","exit"),rng.randint(1,3)):
        s[k]=copy.deepcopy(b[k])
    return s

def structural_batch(count=300,seed=SEED,random_fraction=.65,max_conditions=8):
    permitted_years_for_generation(IST)
    inventory()
    if type(count) is not int or not 1<=count<=50000:raise ValueError("Count invalid")
    if not 0<=random_fraction<=1:raise ValueError("Fraction invalid")
    entries=read_registry()["entries"]
    rng=random.Random(seed)
    seen=set();rows=[];pool=[]
    for i in range(count*100):
        if len(rows)==count:break
        if len(pool)<2 or rng.random()<random_fraction:
            s=strategy(rng,entries,max_conditions)
            lineage={"operator":"RANDOM","parents":[]}
        elif rng.random()<.5:
            parent=rng.choice(pool)
            s=mutate(rng,parent,entries,max_conditions)
            lineage={"operator":"MUTATE","parents":[parent["id"]]}
        else:
            a,b=rng.sample(pool,2)
            s=crossover(rng,a,b)
            lineage={"operator":"CROSSOVER","parents":[a["id"],b["id"]]}
        hashid=sha(s)
        if hashid in seen:continue
        seen.add(hashid)
        s["id"]="NQ26_"+hashid[:16]
        s["lineage"]=lineage
        rows.append(s)
        pool.append(s)
    if len(rows)!=count:raise RuntimeError("Unique AST generation failed")
    return {"schema":"NQ_V26_132_STRUCTURAL_ONLY","status":STATUS,
           "seed":seed,"count":count,
           "candidate_sha256":hashlib.sha256(
              json.dumps(rows,sort_keys=True).encode()).hexdigest(),
           "universe":"NQ_M1","market_data_loaded":False,
           "holdouts_opened":False,"economic_fitness_computed":False,
           "all_132_indicators_certified":False,
           "candidates":rows}

def one_per_indicator(seed=SEED):
    """Guaranteed exact one AST leaf per each of 132 names; no cherry-picking."""
    rng=random.Random(seed)
    entries=read_registry()["entries"]
    return {"schema":"NQ_V26_EACH_REGISTERED_BLOCK_COVERAGE",
       "count":len(entries),"status":STATUS,
       "leaves":[leaf(rng,e) for e in entries],
       "market_data_loaded":False,
       "economic_fitness_computed":False}
