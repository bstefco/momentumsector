from canslim_bot.config import position_size_pct

def test_position_size_pct_default():
    assert position_size_pct() == 12.5

def test_position_size_pct_custom():
    assert position_size_pct(risk_pct=2, stop_pct=0.1) == 20.0 