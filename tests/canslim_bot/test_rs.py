import pytest
import pandas as pd
from canslim_bot.data import rs_rank

def test_rs_rank_ascending():
    series = pd.Series([1, 2, 3, 4, 5])
    rank = rs_rank(series, window=5)
    assert rank == 100.0

def test_rs_rank_descending():
    series = pd.Series([5, 4, 3, 2, 1])
    rank = rs_rank(series, window=5)
    assert rank == pytest.approx(20.0) 