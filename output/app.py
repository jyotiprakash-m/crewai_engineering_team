import gradio as gr
from accounts import Account, get_share_price

# Initialize the account for the demo
account = Account("demo_user")

def create_account(user_id):
    global account
    account = Account(user_id)
    return f"Account created for {user_id}."

def deposit_funds(amount):
    try:
        amount = float(amount)
        account.deposit(amount)
        return f"Successfully deposited ${amount:.2f}. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def withdraw_funds(amount):
    try:
        amount = float(amount)
        account.withdraw(amount)
        return f"Successfully withdrew ${amount:.2f}. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def buy_shares(symbol, quantity):
    try:
        quantity = int(quantity)
        account.buy_shares(symbol.strip().upper(), quantity)
        return f"Successfully bought {quantity} shares of {symbol} at ${get_share_price(symbol):.2f} per share. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def sell_shares(symbol, quantity):
    try:
        quantity = int(quantity)
        account.sell_shares(symbol.strip().upper(), quantity)
        return f"Successfully sold {quantity} shares of {symbol} at ${get_share_price(symbol):.2f} per share. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def get_portfolio_value():
    value = account.portfolio_value()
    holdings = account.holdings_report()
    
    report = f"Cash Balance: ${account.balance:.2f}\n\nHoldings:\n"
    
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        total = price * quantity
        report += f"{symbol}: {quantity} shares @ ${price:.2f} = ${total:.2f}\n"
    
    report += f"\nTotal Portfolio Value: ${value:.2f}"
    return report

def get_profit_loss():
    profit_loss = account.profit_or_loss()
    status = "Profit" if profit_loss >= 0 else "Loss"
    return f"Current {status}: ${abs(profit_loss):.2f}"

def get_holdings():
    holdings = account.holdings_report()
    if not holdings:
        return "No holdings yet."
    
    report = "Current Holdings:\n"
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        total = price * quantity
        report += f"{symbol}: {quantity} shares @ ${price:.2f} = ${total:.2f}\n"
    
    return report

def get_transactions():
    transactions = account.transactions_report()
    if not transactions:
        return "No transactions yet."
    
    report = "Transaction History:\n"
    for transaction in transactions:
        if transaction[0] == 'DEPOSIT':
            report += f"DEPOSIT: ${transaction[1]:.2f}\n"
        elif transaction[0] == 'WITHDRAW':
            report += f"WITHDRAW: ${transaction[1]:.2f}\n"
        elif transaction[0] == 'BUY':
            symbol, quantity, price = transaction[1], transaction[2], transaction[3]
            report += f"BUY: {quantity} shares of {symbol} @ ${price:.2f} = ${quantity * price:.2f}\n"
        elif transaction[0] == 'SELL':
            symbol, quantity, price = transaction[1], transaction[2], transaction[3]
            report += f"SELL: {quantity} shares of {symbol} @ ${price:.2f} = ${quantity * price:.2f}\n"
    
    return report

def get_available_stocks():
    return "Available stocks for demo: AAPL ($150.00), TSLA ($700.00), GOOGL ($2800.00)"

# Building the Gradio UI
with gr.Blocks(title="Trading Account Simulation") as demo:
    gr.Markdown("# Trading Account Simulation")
    gr.Markdown("This is a simple demo of a trading account management system.")
    
    with gr.Tab("Account Management"):
        with gr.Row():
            with gr.Column():
                user_id_input = gr.Textbox(label="User ID", placeholder="Enter your user ID")
                create_btn = gr.Button("Create Account")
                create_output = gr.Textbox(label="Result")
                create_btn.click(create_account, inputs=user_id_input, outputs=create_output)
        
        with gr.Row():
            with gr.Column():
                deposit_input = gr.Number(label="Deposit Amount", precision=2)
                deposit_btn = gr.Button("Deposit")
                deposit_output = gr.Textbox(label="Result")
                deposit_btn.click(deposit_funds, inputs=deposit_input, outputs=deposit_output)
            
            with gr.Column():
                withdraw_input = gr.Number(label="Withdraw Amount", precision=2)
                withdraw_btn = gr.Button("Withdraw")
                withdraw_output = gr.Textbox(label="Result")
                withdraw_btn.click(withdraw_funds, inputs=withdraw_input, outputs=withdraw_output)
    
    with gr.Tab("Trading"):
        gr.Markdown("## Available Stocks")
        stocks_info = gr.Textbox(value=get_available_stocks, label="Stock Information")
        
        with gr.Row():
            with gr.Column():
                buy_symbol = gr.Textbox(label="Symbol", placeholder="e.g., AAPL")
                buy_quantity = gr.Number(label="Quantity", precision=0)
                buy_btn = gr.Button("Buy Shares")
                buy_output = gr.Textbox(label="Result")
                buy_btn.click(buy_shares, inputs=[buy_symbol, buy_quantity], outputs=buy_output)
            
            with gr.Column():
                sell_symbol = gr.Textbox(label="Symbol", placeholder="e.g., AAPL")
                sell_quantity = gr.Number(label="Quantity", precision=0)
                sell_btn = gr.Button("Sell Shares")
                sell_output = gr.Textbox(label="Result")
                sell_btn.click(sell_shares, inputs=[sell_symbol, sell_quantity], outputs=sell_output)
    
    with gr.Tab("Reports"):
        with gr.Row():
            portfolio_btn = gr.Button("Portfolio Value")
            portfolio_output = gr.Textbox(label="Portfolio Value Report")
            portfolio_btn.click(get_portfolio_value, inputs=None, outputs=portfolio_output)
        
        with gr.Row():
            profit_loss_btn = gr.Button("Profit/Loss")
            profit_loss_output = gr.Textbox(label="Profit/Loss Report")
            profit_loss_btn.click(get_profit_loss, inputs=None, outputs=profit_loss_output)
        
        with gr.Row():
            holdings_btn = gr.Button("Current Holdings")
            holdings_output = gr.Textbox(label="Holdings Report")
            holdings_btn.click(get_holdings, inputs=None, outputs=holdings_output)
        
        with gr.Row():
            transactions_btn = gr.Button("Transaction History")
            transactions_output = gr.Textbox(label="Transactions Report")
            transactions_btn.click(get_transactions, inputs=None, outputs=transactions_output)

if __name__ == "__main__":
    demo.launch()