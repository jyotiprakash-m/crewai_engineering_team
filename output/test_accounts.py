import unittest
from unittest.mock import patch
from accounts import Account, get_share_price

class TestSharePrice(unittest.TestCase):
    def test_get_share_price(self):
        # Test known symbols
        self.assertEqual(get_share_price("AAPL"), 150.0)
        self.assertEqual(get_share_price("TSLA"), 700.0)
        self.assertEqual(get_share_price("GOOGL"), 2800.0)
        
        # Test unknown symbol
        self.assertEqual(get_share_price("UNKNOWN"), 0.0)

class TestAccount(unittest.TestCase):
    def setUp(self):
        self.account = Account("test_user")
        
    def test_initialization(self):
        self.assertEqual(self.account.user_id, "test_user")
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(self.account.transactions, [])
    
    def test_deposit(self):
        self.account.deposit(100.0)
        self.assertEqual(self.account.balance, 100.0)
        self.assertEqual(self.account.transactions, [("DEPOSIT", 100.0)])
        
        # Test deposit with negative amount
        with self.assertRaises(ValueError):
            self.account.deposit(-50.0)
            
        # Test deposit with zero amount
        with self.assertRaises(ValueError):
            self.account.deposit(0.0)
    
    def test_withdraw(self):
        self.account.deposit(100.0)
        self.account.withdraw(50.0)
        self.assertEqual(self.account.balance, 50.0)
        self.assertEqual(self.account.transactions, [("DEPOSIT", 100.0), ("WITHDRAW", 50.0)])
        
        # Test withdraw more than balance
        with self.assertRaises(ValueError):
            self.account.withdraw(100.0)
            
        # Test withdraw negative amount
        with self.assertRaises(ValueError):
            self.account.withdraw(-10.0)
            
        # Test withdraw zero amount
        with self.assertRaises(ValueError):
            self.account.withdraw(0.0)
    
    def test_buy_shares(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 2)
        
        # Price of AAPL is 150.0, so 2 shares cost 300.0
        self.assertEqual(self.account.balance, 700.0)
        self.assertEqual(self.account.holdings, {"AAPL": 2})
        self.assertEqual(len(self.account.transactions), 2)
        self.assertEqual(self.account.transactions[1][0], "BUY")
        self.assertEqual(self.account.transactions[1][1], "AAPL")
        self.assertEqual(self.account.transactions[1][2], 2)
        self.assertEqual(self.account.transactions[1][3], 150.0)
        
        # Test buying with insufficient funds
        with self.assertRaises(ValueError):
            self.account.buy_shares("TSLA", 10)  # TSLA at 700.0 x 10 = 7000.0
            
        # Test buying invalid symbol
        with self.assertRaises(ValueError):
            self.account.buy_shares("INVALID", 1)
            
        # Test buying negative quantity
        with self.assertRaises(ValueError):
            self.account.buy_shares("AAPL", -1)
            
        # Test buying zero quantity
        with self.assertRaises(ValueError):
            self.account.buy_shares("AAPL", 0)
    
    def test_sell_shares(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 2)
        self.account.sell_shares("AAPL", 1)
        
        # Price of AAPL is 150.0, so selling 1 share gives 150.0
        self.assertEqual(self.account.balance, 850.0)
        self.assertEqual(self.account.holdings, {"AAPL": 1})
        self.assertEqual(len(self.account.transactions), 3)
        self.assertEqual(self.account.transactions[2][0], "SELL")
        
        # Test selling more shares than owned
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", 2)
            
        # Test selling shares not owned
        with self.assertRaises(ValueError):
            self.account.sell_shares("TSLA", 1)
            
        # Test selling negative quantity
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", -1)
            
        # Test selling zero quantity
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", 0)
            
        # Test complete sell removes from holdings
        self.account.sell_shares("AAPL", 1)
        self.assertNotIn("AAPL", self.account.holdings)
    
    def test_portfolio_value(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 2)  # 300.0 spent, 700.0 remaining
        
        # Portfolio value = balance + value of holdings
        # 700.0 + (2 * 150.0) = 1000.0
        self.assertEqual(self.account.portfolio_value(), 1000.0)
        
        # Add more shares and test again
        self.account.deposit(2200.0)  # Now we have 2900.0
        self.account.buy_shares("GOOGL", 1)  # 2800.0 spent, 100.0 remaining
        # 100.0 + (2 * 150.0) + (1 * 2800.0) = 3200.0
        self.assertEqual(self.account.portfolio_value(), 3200.0)
    
    def test_profit_or_loss(self):
        self.account.deposit(1000.0)
        
        # Initial deposit, no profit or loss yet
        self.assertEqual(self.account.profit_or_loss(), 0.0)
        
        # Buy shares that don't change in value - still no profit/loss
        self.account.buy_shares("AAPL", 2)
        self.assertEqual(self.account.profit_or_loss(), 0.0)
        
        # Mock a price increase and test profit
        with patch("accounts.get_share_price", return_value=200.0):
            # 700.0 + (2 * 200.0) = 1100.0, profit of 100.0
            self.assertEqual(self.account.profit_or_loss(), 100.0)
            
        # Mock a price decrease and test loss
        with patch("accounts.get_share_price", return_value=100.0):
            # 700.0 + (2 * 100.0) = 900.0, loss of 100.0
            self.assertEqual(self.account.profit_or_loss(), -100.0)
    
    def test_holdings_report(self):
        self.account.deposit(5000.0)
        self.account.buy_shares("AAPL", 2)
        self.account.buy_shares("GOOGL", 1)
        
        expected_holdings = {"AAPL": 2, "GOOGL": 1}
        self.assertEqual(self.account.holdings_report(), expected_holdings)
        
        # Ensure the report is a copy, not the actual holdings
        holdings_report = self.account.holdings_report()
        holdings_report["TEST"] = 100
        self.assertNotIn("TEST", self.account.holdings)
    
    def test_transactions_report(self):
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 2)
        self.account.sell_shares("AAPL", 1)
        
        transactions = self.account.transactions_report()
        self.assertEqual(len(transactions), 3)
        
        # Ensure the report is a copy, not the actual transactions
        transactions.append(("TEST", 100))
        self.assertEqual(len(self.account.transactions), 3)


if __name__ == "__main__":
    unittest.main()