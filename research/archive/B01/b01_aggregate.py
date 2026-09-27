from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("results/B01")
files=[ROOT/f"R{i:03d}"/"summary.csv" for i in range(12,16)]
df=pd.concat([pd.read_csv(p) for p in files],ignore_index=True)
p=df["p_value"].astype(float).to_numpy()
order=np.argsort(p); ranked=p[order]; m=len(p)
adj=ranked*m/np.arange(1,m+1)
adj=np.minimum.accumulate(adj[::-1])[::-1]
adj=np.clip(adj,0,1)
q=np.empty(m); q[order]=adj
df["q_value_bh"]=q
df["passes_block_gate"]=df["passes_individual_gate"].astype(bool)&(df["q_value_bh"]<0.05)
ROOT.mkdir(parents=True,exist_ok=True)
df.to_csv(ROOT/"B01_SUMMARY.csv",index=False)

lines=["# B01 Results","",
"| Hypothesis | Experiment | Stage | N | Mean effect | p | q(BH) | Individual gate | Block gate |",
"|---|---|---|---:|---:|---:|---:|---|---|"]
for _,r in df.iterrows():
    lines.append(f"| {r.hypothesis} | {r.experiment} | {r.stage} | {int(r.n)} | {r.mean_effect:.3f} | {r.p_value:.6f} | {r.q_value_bh:.6f} | {bool(r.passes_individual_gate)} | {bool(r.passes_block_gate)} |")
(ROOT/"B01_SUMMARY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(df.to_string(index=False))
