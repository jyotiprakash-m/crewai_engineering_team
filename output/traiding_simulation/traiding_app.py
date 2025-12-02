Your final answer must be the great and the most complete as possible, it must be outcome described.
import io
import threading
from typing import Optional

import gradio as gr

# Import the backend trading engine from traiding_app (assumed in same directory)
from traiding_app import TraidingEngine

# Initialize a single engine instance for the demo (one-user simple prototype)
ENGINE = TraidingEngine(seed=42, starting_cash=100000.0)
# Start background market simulation so prices move "live" for the demo
ENGINE.start_market_simulation(background=True, interval=1.0)


# Utility to format portfolio snapshot into HTML
def portfolio_to_html(pf: dict) -> str:
    html = []
    html.append("<h3>Portfolio Summary</h3>")
    html.append(f"<b>Cash:</b> ${pf['cash']:.2f}<br/>")
    html.append(f"<b>Equity:</b> ${pf['equity']:.2f}<br/>")
    html.append(f"<b>Realized P/L:</b> ${pf['realized_pnl']:.2f}<br/>")
    html.append(f"<b>Unrealized P/L:</b> ${pf['unrealized_pnl']:.2f}<br/>")
    html.append("<hr/>")
    html.append("<h4>Positions</h4>")
    if not pf['positions']:
        html.append("<i>No open positions</i><br/>")
    else:
        html.append("<table border='1' style='border-collapse: collapse;'>")
        html.append("<tr><th>Symbol</th><th>Qty</th><th>Avg Price</th><th>Market Price</th><th>Market Value</th><th>Unrealized P/L</th></tr>")
        for s, pos in pf['positions'].items():
            html.append("<tr>")
            html.append(f"<td>{s}</td>")
            html.append(f"<td>{pos['quantity']}</td>")
            html.append(f"<td>${pos['avg_price']:.2f}</td>")
            html.append(f"<td>${pos['market_price']:.2f}</td>")
            html.append(f"<td>${pos['market_value']:.2f}</td>")
            upnl = pos['unrealized_pnl']
            color = "green" if upnl >= 0 else "red"
            html.append(f"<td><span style='color:{color};'>${upnl:.2f}</span></td>")
            html.append("</tr>")
        html.append("</table>")
    html.append("<hr/>")
    open_cond = pf.get('open_conditionals', [])
    html.append("<h4>Open Conditional Orders (Stop-loss / Take-profit)</h4>")
    if not open_cond:
        html.append("<i>No open conditional orders</i><br/>")
    else:
        html.append("<ul>")
        for c in open_cond:
            sl = c.get('stop_loss')
            tp = c.get('take_profit')
            html.append(f"<li>{c['symbol']} qty {c['quantity']} — SL: {sl if sl is not None else '—'} TP: {tp if tp is not None else '—'} (id={c['id']})</li>")
        html.append("</ul>")
    html.append("<hr/>")
    html.append("<h4>Recent Trades</h4>")
    if not pf.get('trade_history'):
        html.append("<i>No trades yet</i>")
    else:
        html.append("<table border='1' style='border-collapse: collapse;'>")
        html.append("<tr><th>Time</th><th>Side</th><th>Symbol</th><th>Qty</th><th>Price</th><th>Realized P/L</th></tr>")
        for t in reversed(pf['trade_history'][-20:]):
            ts = t.get('timestamp')
            side = t.get('side')
            sym = t.get('symbol')
            qty = t.get('quantity')
            pr = t.get('price')
            r = t.get('realized_pnl', '')
            html.append(f"<tr><td>{ts}</td><td>{side}</td><td>{sym}</td><td>{qty}</td><td>${pr:.2f}</td><td>{f'${r:.2f}' if r != '' else ''}</td></tr>")
        html.append("</table>")
    return "".join(html)


# Helper to get price chart bytes for gradio Image
def get_price_chart_bytes(symbol: str) -> Optional[bytes]:
    try:
        b = ENGINE.get_price_chart(symbol)
        return b
    except Exception:
        return None


def get_portfolio_chart_bytes() -> Optional[bytes]:
    try:
        b = ENGINE.get_portfolio_chart()
        return b
    except Exception:
        return None


# Main function to refresh dashboard pieces for a given symbol
def refresh_dashboard(symbol: str):
    try:
        price = ENGINE.get_market_price(symbol)
        price_text = f"{symbol} price: ${price:.2f}"
    except Exception as e:
        price_text = f"Error fetching price: {e}"
    price_img = get_price_chart_bytes(symbol)
    pf = ENGINE.get_portfolio()
    pf_html = portfolio_to_html(pf)
    port_img = get_portfolio_chart_bytes()
    return price_text, price_img, pf_html, port_img


# Function to place an order and then return result + refreshed dashboard
def place_order(symbol: str, side: str, quantity: float, stop_loss: Optional[float], take_profit: Optional[float]):
    # Normalization: accept empty strings or None for SL/TP
    sl = float(stop_loss) if stop_loss not in (None, "", "None") and str(stop_loss).strip() != "" else None
    tp = float(take_profit) if take_profit not in (None, "", "None") and str(take_profit).strip() != "" else None

    try:
        msg = ENGINE.place_order(symbol, side.lower(), float(quantity), stop_loss=sl, take_profit=tp)
        status = f"Order result: {msg}"
    except Exception as e:
        status = f"Error placing order: {e}"

    # After placing the order, refresh market snapshot and portfolio
    price_text, price_img, pf_html, port_img = refresh_dashboard(symbol)
    return status, price_text, price_img, pf_html, port_img


# Simple start/stop control for the background simulation
def start_simulation():
    ENGINE.start_market_simulation(background=True)
    return "Simulation started"


def stop_simulation():
    ENGINE.stop_market_simulation()
    return "Simulation stopped"


# Build the Gradio interface
with gr.Blocks(title="Demo Traiding App (Prototype)", css="""
#title {text-align: center; margin-bottom: 10px;}
.row {display:flex; gap: 20px;}
.left, .right {flex: 1;}
img {max-width: 100%;}
""") as demo:
    gr.Markdown("<h1 id='title'>Demo Traiding App — Simulated Trading Engine</h1>")
    gr.Markdown("This is a simple prototype for demo/testing only. Prices are simulated with a random walk. Do not use for real trading.")

    # Top controls and market view
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Market")
            symbol_dropdown = gr.Dropdown(label="Symbol", choices=ENGINE.list_symbols(), value=ENGINE.list_symbols()[0])
            price_display = gr.Textbox(label="Current Price", interactive=False)
            price_chart = gr.Image(label="Price Chart", type="bytes")
            refresh_btn = gr.Button("Refresh")
            start_btn = gr.Button("Start Simulation")
            stop_btn = gr.Button("Stop Simulation")
        with gr.Column(scale=1):
            gr.Markdown("### Place Order")
            side_radio = gr.Radio(label="Side", choices=["buy", "sell"], value="buy", type="value")
            qty_number = gr.Number(label="Quantity", value=1.0)
            sl_number = gr.Textbox(label="Stop-loss Price (optional)", placeholder="e.g. 140.0")
            tp_number = gr.Textbox(label="Take-profit Price (optional)", placeholder="e.g. 160.0")
            place_btn = gr.Button("Place Order")
            order_result = gr.Textbox(label="Order Result", interactive=False)

    # Portfolio and charts
    gr.Markdown("### Portfolio & Activity")
    with gr.Row():
        portfolio_html = gr.HTML()
        portfolio_chart = gr.Image(label="Portfolio Equity Chart", type="bytes")

    # Wiring actions
    # Initial refresh on load
    def initial_load(symbol):
        return refresh_dashboard(symbol)

    refresh_btn.click(fn=lambda s: refresh_dashboard(s), inputs=[symbol_dropdown], outputs=[price_display, price_chart, portfolio_html, portfolio_chart])
    symbol_dropdown.change(fn=lambda s: refresh_dashboard(s), inputs=[symbol_dropdown], outputs=[price_display, price_chart, portfolio_html, portfolio_chart])

    place_btn.click(fn=lambda s, side, qty, sl, tp: place_order(s, side, qty, sl, tp),
                    inputs=[symbol_dropdown, side_radio, qty_number, sl_number, tp_number],
                    outputs=[order_result, price_display, price_chart, portfolio_html, portfolio_chart])

    start_btn.click(fn=lambda: (start_simulation(),), inputs=None, outputs=[order_result])
    stop_btn.click(fn=lambda: (stop_simulation(),), inputs=None, outputs=[order_result])

    # Run initial refresh to populate UI elements when app starts
    demo.load(fn=initial_load, inputs=[symbol_dropdown], outputs=[price_display, price_chart, portfolio_html, portfolio_chart])

# Launch the demo
if __name__ == "__main__":
    demo.launch()