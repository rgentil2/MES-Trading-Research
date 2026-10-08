import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from mes_intraday_floating_audit import (parse_nt_time,parse_money,Trade,Bar,apply_router,replay)

D=datetime

class MFFUAuditTests(unittest.TestCase):
 def test_localized(self):
  self.assertEqual(parse_nt_time('29/01/2020 10:02:00 a\u00a0m'),D(2020,1,29,10,2))
  self.assertEqual(parse_nt_time('10/07/2020 12:05:00 p m'),D(2020,7,10,12,5))
  self.assertEqual(parse_money('-$ 55,63'),-55.63)
  self.assertEqual(parse_money('$ 1.880,50'),1880.5)
 def test_router_excludes_simultaneous_opposition(self):
  d=D(2021,2,9,10,2)
  a=Trade('PDC:1','PDC',1,d,d+timedelta(minutes=3),100,99,-6.90,5)
  b=Trade('POC:1','POC',-1,d+timedelta(minutes=1),d+timedelta(minutes=6),101,100,3.10,5)
  sel,skips=apply_router([a,b],True)
  self.assertEqual(len(sel),1)
  self.assertEqual(len(skips),1)
 def test_minute_floating_risk_replay(self):
  d=D(2020,1,29,10,0)
  t=Trade('PDC:1','PDC',1,d,d+timedelta(minutes=2),100.0,101.0,3.10,1.0)
  bars={d+timedelta(minutes=1):Bar(d+timedelta(minutes=1),100,101,98,100,'MAR20'),
   d+timedelta(minutes=2):Bar(d+timedelta(minutes=2),100,101,99,101,'MAR20')}
  result=replay([t],bars)
  self.assertEqual(result['float_min_margin_above_MFFU_floor_usd'],1988.1)
  self.assertEqual(result['final_balance_net'],3.1)
  self.assertEqual(result['adverse_one_minute_equity_breach_count'],0)
 def test_paired_same_underlying_worst_uses_single_price(self):
  d=D(2020,1,29,10,0)
  a=Trade('PDC:1','PDC',1,d,d+timedelta(minutes=1),100.0,101,3.1,1)
  b=Trade('POC:1','POC',-1,d,d+timedelta(minutes=1),101.0,100,3.1,1)
  ts=d+timedelta(minutes=1)
  bars={ts:Bar(ts,100,105,95,100,'MAR20')}
  result=replay([a,b],bars)
  self.assertEqual(result['float_min_margin_above_MFFU_floor_usd'],2001.2)
 def test_missing_bar_blocks(self):
  d=D(2020,1,29,10,0)
  t=Trade('PDC:1','PDC',1,d,d+timedelta(minutes=2),100,101,3.1,1)
  bars={d+timedelta(minutes=1):Bar(d+timedelta(minutes=1),100,101,99,100,'MAR20')}
  res=replay([t],bars)
  self.assertEqual(res['trading_days_processed'],0)
  self.assertEqual(len(res['missing_path_days']),1)
if __name__=='__main__':unittest.main()