#!/usr/bin/env python3
"""One-off registration, official immutable family freeze; no market data reads."""
import json
from pathlib import Path
from tools.research_governance import freeze_family,preflight_family

id='NQ-PARENT-INTERACTIONS-H59-H66-V1'
ledger_file=Path('research/SEARCH_LEDGER.json')
ledger=json.loads(ledger_file.read_text())
if len(ledger['future_families'])!=4 or any(f['id']==id for f in ledger['future_families']):
    raise RuntimeError('Family order inconsistent: do not change locked history')
pre='research/nq/NQ_H59_H66_PARENT_INTERACTIONS_PREREG_2026_10_10.md'
defs=[
  'H55 and H56 simultaneous matching directional signal at 09:45; take H55 once',
  'H55 at 09:45, H56 absent at 09:45; use H55 side',
  'H56 at 09:45, H55 absent at 09:45; use H56 side',
  'H09 at 09:45, H55 and H56 absent at 09:45; use H09 side',
  'H09 and H56 at 09:45 same directional side; one H09 position',
  'H29 at 10:00, neither H55 nor H56 at 09:45; take H29 side',
  'H54 signal after 09:45 and H55 pre-existing same directional side; H54 position',
  'H54 signal after 09:45 and H55 pre-existing opposite directional side; H54 position'
]
ids=[f'NQ-H{n}' for n in range(59,67)]
entries=[dict(id=i,preregistration_path=pre,research_instrument='NQ',analysis_kind='DIRECTIONAL',execution_instrument=None,definition=definition,alternative='Net directional mean return over 30 minutes exceeds zero after 25.74 USD NQ Free friction',endpoint='Frozen parent-signal next-minute OPEN to +30m OPEN, one-sided weekly signflip, bootstrap 90% CI, whole-family BH (8)') for i,definition in zip(ids,defs)]
family=dict(id=id,index=5,question='Does ex-ante concurrence/exclusion among prior opening-gap, overnight-VWAP and premarket signals change NQ net 30-minute directional effectiveness?',origin_units=ids,data_role='REUSED_DEVELOPMENT',independent_inference_justification='Parents and some overlapping outcomes already inspected on reused 2020–2024, no independent inference; 2025/26 strictly sealed',members=entries,definition_files=[pre,'research/nq/nq_h59_h66_parent_interactions.py','research/nq/test_nq_h59_h66_parent_interactions.py','research/nq/nq_h08_h32_minute_2020_2024.py','research/nq/nq_h53_h58.py'],result_artifacts=['results/development/nq_h59_h66_family.json'])
ledger['future_families'].append(family)
ledger_file.write_text(json.dumps(ledger,indent=2)+'\n')
lock=freeze_family(Path.cwd(),id)
preflight_family(Path.cwd(),id)
print(json.dumps({'status':'FROZEN','id':id,'n':len(ids),'alpha':lock['alpha'],'family_sha256':lock['family_sha256']}))