from typing import List, Dict, Tuple, Union, Optional

# Mock implementation of get_share_price, in practice this should be provided.
def get_share_price(symbol: str) -> float:
    """
    Get the current price of a share.
    
    :param symbol: The stock symbol.
    :return: The current price of the share.
    """
    share_prices = {
        'AAPL': 150.0,
        'TSLA': 700.0,
        'GOOGL': 2800.0
    }
    return share_prices.get(symbol, 0.0)


class Account:
    """
    A class representing a user's trading account.
    
    This class manages deposits, withdrawals, buying and selling of shares,
    and provides reporting on holdings, transactions, and profit/loss.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize a new account for the user.
        
        :param user_id: The unique identifier for the user.
        """
        self.user_id = user_id
        self.balance = 0.0
        self.holdings: Dict[str, int] = {}  # Dictionary to hold symbol: quantity
        self.transactions: List[Tuple] = []  # List of transactions

    def deposit(self, amount: float) -> None:
        """
        Deposit funds into the user's account.

        :param amount: The amount to deposit.
        :raises ValueError: If the amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transactions.append(('DEPOSIT', amount))

    def withdraw(self, amount: float) -> None:
        """
        Withdraw funds from the user's account.

        :param amount: The amount to withdraw.
        :raises ValueError: If the withdrawal amount is not positive or greater than the balance.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance < amount:
            raise ValueError("Insufficient funds to withdraw.")
        self.balance -= amount
        self.transactions.append(('WITHDRAW', amount))

    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Buy a specified quantity of shares.

        :param symbol: The stock symbol.
        :param quantity: The number of shares to buy.
        :raises ValueError: If the quantity is not positive, the symbol is unknown,
                           or there are insufficient funds.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        price = get_share_price(symbol)
        if price == 0.0:
            raise ValueError(f"Unknown symbol: {symbol}")
            
        total_cost = price * quantity
        if self.balance < total_cost:
            raise ValueError(f"Insufficient funds to buy shares. Required: {total_cost}, Available: {self.balance}")
            
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append(('BUY', symbol, quantity, price))

    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Sell a specified quantity of shares.

        :param symbol: The stock symbol.
        :param quantity: The number of shares to sell.
        :raises ValueError: If the quantity is not positive or attempting to sell more shares than owned.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
            
        if symbol not in self.holdings:
            raise ValueError(f"No shares of {symbol} owned.")
            
        if self.holdings[symbol] < quantity:
            raise ValueError(f"Insufficient shares to sell. Owned: {self.holdings[symbol]}, Requested: {quantity}")
            
        price = get_share_price(symbol)
        self.balance += price * quantity
        self.holdings[symbol] -= quantity
        
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
            
        self.transactions.append(('SELL', symbol, quantity, price))

    def portfolio_value(self) -> float:
        """
        Calculate the total value of the portfolio (cash balance + value of all holdings).

        :return: The total value of the user's portfolio.
        """
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def profit_or_loss(self) -> float:
        """
        Calculate the profit or loss from the initial deposit.
        This is the difference between the current portfolio value and the sum of all deposits.

        :return: The profit or loss.
        """
        total_deposits = 0.0
        for transaction in self.transactions:
            if transaction[0] == 'DEPOSIT':
                total_deposits += transaction[1]
        return self.portfolio_value() - total_deposits

    def holdings_report(self) -> Dict[str, int]:
        """
        Report the current holdings of the user.

        :return: A dictionary of stock symbol to quantity owned.
        """
        return self.holdings.copy()

    def transactions_report(self) -> List[Tuple]:
        """
        List all transactions made by the user.

        :return: A list of transactions.
        """
        return self.transactions.copy()