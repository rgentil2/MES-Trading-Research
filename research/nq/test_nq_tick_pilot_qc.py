import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
from tempfile import TemporaryDirectory
from nq_tick_pilot_qc import check_safe_path, parse_nt_tick_row, inspect
from datetime import date

class TickQCSourceOnlyTests(unittest.TestCase):
 def test_parse_seconds_and_100ns(self):
  a=parse_nt_tick_row('20240206 143000;17890.25;2')
  b=parse_nt_tick_row('20240206 143000 0000001;17890.25;2')
  self.assertEqual(b[0]-a[0],1)
 def test_timestamp_2025_rejected(self):
  with self.assertRaises(ValueError): parse_nt_tick_row('20250205 143000;17999.00;1')
 def test_quote_and_trade_contracts(self):
  self.assertEqual(check_safe_path(Path('private/development_2020_2024/NQ 03-24.Last.txt'),'Last'),'NQ 03-24')
  with self.assertRaises(ValueError): check_safe_path(Path('private/development_2020_2024/NQ 03-24.Last.txt'),'Bid')
 def test_2025_path_rejected_before_read(self):
  with self.assertRaises(ValueError): check_safe_path(Path('private/development_2025/NQ 03-25.Last.txt'),'Last')
  with self.assertRaises(ValueError): check_safe_path(Path('private/development_2020_2024/2026/NQ 03-24.Last.txt'),'Last')
 def test_no_cross_contract(self):
  with self.assertRaises(ValueError): check_safe_path(Path('private/development_2020_2024/NQ 06-24.Bid.txt'),'Bid','NQ 03-24')
 def test_utc_to_et_with_stated_pilot_window(self):
  with TemporaryDirectory() as d:
   base=Path(d)/'development_2020_2024';base.mkdir()
   p=base/'NQ 03-24.Last.txt'
   p.write_text('20240206 132959;17890.00;1\n20240206 133000 1000000;17890.25;1\n20240206 162959;17890.50;2\n20240206 163000;17890.75;1\n',encoding='utf-8')
   x=inspect(p,'Last',date(2024,2,5),date(2024,2,16))
   self.assertEqual(x['rows_in_pilot'],2)
   self.assertEqual(x['daily_active_minute_counts']['2024-02-06'],2)
   self.assertEqual(x['quality_status'],'PRELIMINARY_PASS')
 def test_detect_out_of_order(self):
  with TemporaryDirectory() as d:
   base=Path(d)/'development_2020_2024';base.mkdir();p=base/'NQ 03-24.Last.txt'
   p.write_text('20240206 143001;17890.00;1\n20240206 143000;17890.25;1\n')
   x=inspect(p,'Last',date(2024,2,6),date(2024,2,6))
   self.assertEqual(x['out_of_order'],1)
   self.assertEqual(x['quality_status'],'REJECT')
 def test_negative_volume_invalid(self):
  with self.assertRaises(ValueError):parse_nt_tick_row('20240206 143000;17890.00;-1')
 def test_invalid_price_grid_detected(self):
  with TemporaryDirectory() as d:
   p=Path(d)/'development_2020_2024'/'NQ 03-24.Last.txt';p.parent.mkdir()
   p.write_text('20240206 143000;17890.10;1\n')
   x=inspect(p,'Last',date(2024,2,6),date(2024,2,6))
   self.assertEqual(x['non_quarter_tick'],1)
   self.assertEqual(x['quality_status'],'REJECT')

if __name__=='__main__': unittest.main()