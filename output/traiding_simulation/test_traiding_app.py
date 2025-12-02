import pytest
from TraidingEngine import TraidingEngine


def test_get_market_price_and_unknown():
    engine = TraidingEngine(seed=42)
    price = engine.get_market_price('AAPL')
    assert isinstance(price, float)
    with pytest.raises(KeyError):
        engine.get_market_price('UNKNOWN_SYMBOL')


def test_add_symbol_and_list():
    engine = TraidingEngine(seed=1)
    engine.add_symbol('TESTSYM', 12.34)
    assert 'TESTSYM' in engine.list_symbols()
    assert engine.get_market_price('TESTSYM') == pytest.approx(12.34)


def test_place_buy_and_portfolio_and_conditional_creation():
    engine = TraidingEngine(seed=1, starting_cash=10000.0)
    price = engine.get_market_price('AAPL')
    # simple buy
    res = engine.place_order('AAPL', 'buy', 1.0)
    assert 'buy executed' in res
    assert 'AAPL' in engine.portfolio
    assert engine.portfolio['AAPL']['quantity'] == pytest.approx(1.0)
    # buy with stop_loss / take_profit creates a conditional order
    res2 = engine.place_order('AAPL', 'buy', 1.0, stop_loss=100.0, take_profit=300.0)
    assert 'conditional' in res2
    open_conds = engine.get_open_conditionals()
    assert any(c['symbol'] == 'AAPL' and c['status'] == 'open' for c in open_conds)


def test_place_buy_insufficient_cash_raises():
    engine = TraidingEngine(starting_cash=0.01)
    with pytest.raises(ValueError):
        engine.place_order('AAPL', 'buy', 1.0)


def test_place_sell_flow_and_realized_pnl():
    engine = TraidingEngine(starting_cash=10000.0)
    # buy 2 shares
    engine.place_order('AAPL', 'buy', 2.0)
    avg_price = engine.portfolio['AAPL']['avg_price']
    # sell 1 share
    before_cash = engine.cash
    sell_result = engine.place_order('AAPL', 'sell', 1.0)
    assert 'sell executed' in sell_result
    # cash increased by current market price
    cur_price = engine.get_market_price('AAPL')
    assert engine.cash == pytest.approx(before_cash + cur_price)
    # portfolio quantity decreased
    qty = engine.portfolio.get('AAPL', {}).get('quantity', 0.0)
    assert qty == pytest.approx(1.0)
    # realized_pnl updated (could be zero if price equals avg)
    assert isinstance(engine.realized_pnl, float)


def test_validate_order_edge_cases():
    engine = TraidingEngine()
    ok, msg = engine.validate_order('AAPL', 'invalid_type', 1.0)
    assert not ok
    ok2, msg2 = engine.validate_order('UNKNOWN', 'buy', 1.0)
    assert not ok2
    ok3, msg3 = engine.validate_order('AAPL', 'sell', 1000000)
    assert not ok3


def test_conditional_sell_triggering():
    engine = TraidingEngine(starting_cash=100000.0)
    # buy one AAPL with a stop loss slightly below current price
    current = engine.get_market_price('AAPL')
    stop = current - 5.0
    engine.place_order('AAPL', 'buy', 1.0, stop_loss=stop)
    open_conds = engine.get_open_conditionals()
    assert len(open_conds) >= 1
    cond = open_conds[0]
    assert cond['status'] == 'open'
    # move market below stop and trigger
    engine.market_data['AAPL'] = stop - 1.0
    engine._check_conditional_orders()
    # conditional should have been triggered (or cancelled if no holding)
    assert cond['status'] in ('triggered', 'cancelled')
    # if triggered, ensure portfolio reduced
    if cond['status'] == 'triggered':
        assert 'AAPL' not in engine.portfolio or engine.portfolio.get('AAPL', {}).get('quantity', 0) == 0


def test_calculate_profit_loss_unrealized_and_realized():
    engine = TraidingEngine(starting_cash=100000.0)
    engine.place_order('AAPL', 'buy', 2.0)
    avg = engine.portfolio['AAPL']['avg_price']
    # increase market price by a known amount
    engine.market_data['AAPL'] = avg + 10.0
    pl = engine.calculate_profit_loss()
    assert pl == pytest.approx(20.0)
    # realize P/L by selling
    engine.place_order('AAPL', 'sell', 2.0)
    assert engine.realized_pnl == pytest.approx(20.0)


def test_price_and_portfolio_charts_generation():
    engine = TraidingEngine()
    img = engine.get_price_chart('AAPL')
    assert isinstance(img, (bytes, bytearray)) and len(img) > 0
    pimg = engine.get_portfolio_chart()
    assert isinstance(pimg, (bytes, bytearray)) and len(pimg) > 0


def test_price_chart_missing_raises():
    engine = TraidingEngine()
    with pytest.raises(KeyError):
        engine.get_price_chart('NONEXISTENT')


def test_portfolio_chart_no_history_raises():
    engine = TraidingEngine()
    # clear recorded history and then call
    engine.portfolio_history.clear()
    with pytest.raises(ValueError):
        engine.get_portfolio_chart()


def test_simulate_market_changes_appends_history():
    engine = TraidingEngine(seed=0)
    initial_len = len(engine.price_history['AAPL'])
    engine.simulate_market_changes(steps=2, interval=0.0)
    assert len(engine.price_history['AAPL']) >= initial_len + 2