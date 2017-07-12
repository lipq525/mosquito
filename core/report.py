from termcolor import colored
from datetime import datetime
import pandas as pd


class Report:
    """
    Main reporting class (overall score and plots)
    """

    initial_closing_prices = None
    initial_balance = 0.0
    verbosity = 1

    def __init__(self, initial_wallet, pairs, root_report_currency):
        self.initial_wallet = initial_wallet
        self.pairs = pairs
        self.initial_closing_prices = pd.DataFrame()
        self.root_report_currency = root_report_currency

    def set_verbosity(self, verbosity):
        self.verbosity = verbosity

    def calc_stats(self, ticker_data, wallet):
        """
        Creates ticker report
        """
        # Store initial closing price and initial overall wallet balance
        if len(self.initial_closing_prices.index) < len(self.pairs):
            self.initialize_start_price(ticker_data)
            self.initial_balance = self.initialize_start_balance(self.initial_wallet,
                                                                 self.initial_closing_prices)
        # print('ticker_data....', ticker_data)
        date_time = datetime.fromtimestamp(ticker_data['date'][0]).strftime('%c') + ','
        current_close = 'close:' + format(ticker_data.iloc[0]['close'], '2f') + ','
        # Wallet
        wallet_text = self.get_wallet_text(wallet)
        # Balance
        balance = self.calc_balance(ticker_data, wallet.current_balance)
        balance_text = self.get_color_text('$: ', balance) + ','
        # Buy & Hold
        bh = self.calc_buy_and_hold(ticker_data, wallet.initial_balance)
        bh_text = self.get_color_text('b&h: ', bh)
        print(date_time,
              current_close,
              wallet_text,
              balance_text,
              bh_text)

        return 0

    @staticmethod
    def get_wallet_text(wallet, currencies=None):
        """
        Returns wallet balance in string. By default it returns balance of the entire wallet.
        You can specify currencies which you would like to receive update
        """
        # TODO return only wallet of given currencies
        wallet_string = ''
        for symbol, balance in wallet.current_balance.items():
            if balance > 0:
                wallet_string += ' | ' + str(balance) + symbol
        wallet_string += ' |'
        return wallet_string

    @staticmethod
    def get_color_text(text, value):
        """
        Returns colored text
        """
        v = round(value, 2) + 0.0
        output_text = text + str(round(v, 2)) + '%'
        color = 'green' if round(v, 2) >= 0 else 'red'
        return colored(output_text, color)

    def get_exchange_rate_value(self, currency, ticker_data, value, root_currency):
        """
        Returns currencies exchange value towards the root_currency
        """
        # 1) If currency is root one, just return it
        if currency == root_currency:
            return value
        # 2) If we have exchange rate towards root_currency, return that one
        pair = root_currency + '_' + currency
        pair_tick = ticker_data.loc[ticker_data.pair == pair]
        # pair_tick = ticker_data.loc[ticker_data['pair'] == pair]
        if not pair_tick.empty:
            closing_price = pair_tick['close'].iloc[0]
            return closing_price * value
        # 3) If we didn't find root find exchange rate to BTC and then to root
        btc_pair = 'BTC_' + currency
        btc_tick = ticker_data.loc[ticker_data['pair'] == btc_pair]
        if currency != 'BTC' and not btc_tick.empty:
            # If we have found it, get roots exchange value
            closing_price = btc_tick['close'].iloc[0]
            btc_value = closing_price * value
            rate_value = self.get_exchange_rate_value('BTC', ticker_data, btc_value, root_currency)
            return rate_value

        if self.verbosity > 0:
            print("Couldn't find exchange rate for:", currency)
        return 0.0

    def calc_balance(self, ticker_data, wallet_balance):
        """
        Calculates current balance (profit/loss)
        """
        current_balance = 0
        for currency, value in wallet_balance.items():
            pair_value = self.get_exchange_rate_value(currency, ticker_data, value, self.root_report_currency)
            current_balance += pair_value

        price_diff = current_balance - self.initial_balance
        if self.initial_balance == 0.0:
            return 0.0
        perc_change = ((price_diff*100.0)/self.initial_balance)
        return perc_change

    def initialize_start_price(self, ticker_data):
        """
        Save initial closing price
        """
        # Get only currencies that have not been initialized yet
        for index, row in ticker_data.iterrows():
            pair = row['pair']
            if self.initial_closing_prices.empty:
                self.initial_closing_prices = self.initial_closing_prices.append(row, ignore_index=True)
            elif self.initial_closing_prices.pair[self.initial_closing_prices.pair == pair].count() == 0:
                self.initial_closing_prices = self.initial_closing_prices.append(row, ignore_index=True)

    def initialize_start_balance(self, wallet, close_prices):
        """
        Calculate overall wallet balance in bitcoins
        """
        balance = 0.0
        for currency, value in wallet.items():
            pair_value = self.get_exchange_rate_value(currency, close_prices, value, self.root_report_currency)
            balance += pair_value
        return balance

    def calc_buy_and_hold(self, ticker_data, initial_balance):
        """
        Calculate Buy & Hold price
        """
        return self.calc_balance(ticker_data, initial_balance)
