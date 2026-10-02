import numpy as np
import pandas as pd
import pytest
from src.es_microstructure import attach_bbo_to_trades, classify_aggressor, aggregate_flow


def stamp(values):
    return pd.to_datetime(values, utc=True)


def test_quotes_from_expired_contract_cannot_attach_to_new_contract():
    trades = pd.DataFrame({'timestamp':stamp(['2024-06-03 13:30:01']), 'contract':['ES SEP24'],
                           'price':[5100.25], 'volume':[2]})
    bids = pd.DataFrame({'timestamp':stamp(['2024-06-03 13:30:00']), 'contract':['ES JUN24'], 'price':[5100.]})
    asks = bids.assign(price=5100.25)
    result = classify_aggressor(attach_bbo_to_trades(trades, bids, asks))
    assert result['bid'].isna().all() and result['ask'].isna().all()
    assert result['aggressor_side'].tolist() == [0]


def test_interleaved_contracts_receive_only_their_own_backward_quotes():
    trades = pd.DataFrame({'timestamp':stamp(['2024-06-03 13:30:01']*2),
                           'contract':['ES JUN24','ES SEP24'], 'price':[5000.25,5100.], 'volume':[2,3]})
    bids = pd.DataFrame({'timestamp':stamp(['2024-06-03 13:30:00']*2),
                         'contract':['ES JUN24','ES SEP24'], 'price':[5000.,5100.]})
    asks = bids.assign(price=[5000.25,5100.25])
    result = classify_aggressor(attach_bbo_to_trades(trades, bids, asks))
    assert result['aggressor_side'].tolist() == [1,-1]
    flow = aggregate_flow(result)
    assert flow.loc['ES JUN24']['delta'].iloc[0] == 2
    assert flow.loc['ES SEP24']['delta'].iloc[0] == -3
    assert len(flow) == 2


def test_contract_identity_is_mandatory():
    frame = pd.DataFrame({'timestamp':stamp(['2024-06-03 13:30:01']), 'price':[5000.], 'volume':[2]})
    with pytest.raises(ValueError, match='contract'):
        attach_bbo_to_trades(frame, frame, frame)


def test_locked_book_is_unclassified_instead_of_becoming_sell_by_overwrite():
    frame = pd.DataFrame({'price':[5000.], 'volume':[4], 'bid':[5000.], 'ask':[5000.]})
    result = classify_aggressor(frame)
    assert result['aggressor_side'].tolist() == [0]
    assert result['signed_volume'].tolist() == [0]


def test_crossed_and_nonfinite_books_abort_qc():
    frame = pd.DataFrame({'price':[5000.], 'volume':[4], 'bid':[5000.25], 'ask':[5000.]})
    with pytest.raises(ValueError, match='crossed'):
        classify_aggressor(frame)
    with pytest.raises(ValueError, match='nonfinite'):
        classify_aggressor(frame.assign(bid=np.inf))
