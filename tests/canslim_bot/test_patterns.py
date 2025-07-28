import pandas as pd
from canslim_bot.patterns import compute_pivot

def test_compute_pivot_valid():
    # Synthetic valid cup-with-handle: base 20w, handle last 3w in upper half
    data = {
        'High': [10]*17 + [12, 13, 14],
        'Low': [7]*20,
        'Close': [8]*17 + [13, 13.5, 14],
    }
    df = pd.DataFrame(data)
    pivot = compute_pivot(df)
    assert pivot == 14.0

def test_compute_pivot_invalid():
    # Too deep base
    data = {
        'High': [10]*17 + [12, 13, 14],
        'Low': [2]*20,
        'Close': [3]*20,
    }
    df = pd.DataFrame(data)
    pivot = compute_pivot(df)
    assert pivot is None 