import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from utilities import compute_year_fraction

class yfDataLoader:

    def __init__(self, ticker:str):

        self.ticker = ticker
        self.yfticker = yf.Ticker(self.ticker)
        self.riskFreeRates_dict = self.load_rf_curve()


    @staticmethod
    def load_rf_curve():
        rate_data = {'^IRX': 0.25, '^FVX': 5.0, '^TNX': 10.0}
        rates = {0.25:None, 5.0:None, 10.0:None}
        for ticker, maturity in rate_data.items():
            df = yf.download(ticker, period='5d', interval='1d', progress=False, auto_adjust=True)
            last_valid_close = df['Close'].dropna().iloc[-1]

            rates[maturity] = float(last_valid_close.values[0]) / 100.0
        
        return rates
        
    def rate_interpolator(self):
        maturities = np.array(sorted(self.riskFreeRates_dict.keys()))
        rate_values = np.array([self.riskFreeRates_dict[m] for m in maturities])
        return lambda T: float(np.interp(float(T), maturities, rate_values))


    def get_current_price(self):
        try:
            return self.yfticker.fast_info["last_price"]
        except:
            hist = self.yfticker.history(period="1d")
            if not hist.empty:
                return hist["Close"].iloc[-1]
            return None
    
    def get_dividend_yield(self):
        try:
            dividends = self.yfticker.dividends
            if len(dividends) == 0:
                return 0.0
            last_year = dividends[dividends.index > pd.Timestamp.today() - pd.DateOffset(years=1)]
            annual_dividend = last_year.sum()
            price = self.get_current_price()
            return annual_dividend / price if price else 0.0
        except:
            return 0.0
        
    def get_maturity(self, contract_symbol):

        #TODO remove it, not necessary ciclying on maturity date already, just compute year fraction

        contract_symbol = contract_symbol.removeprefix(self.ticker)
        if contract_symbol[0] =="W":
            contract_symbol = contract_symbol[1:7]
        else: 
            contract_symbol = contract_symbol[:6]
        maturity_date = datetime.strptime(contract_symbol, "%y%m%d")
        maturity = compute_year_fraction(datetime.today(), maturity_date + timedelta(days=1))

        return maturity
            
    def get_option_chain(self, moneyness=0.3):

        option_expiries = self.yfticker.options
        current_price = self.get_current_price()
        q = self.get_dividend_yield()


        calls_dfs = []
        puts_dfs = []

        for expiry in option_expiries:
            calls_df = pd.DataFrame(self.yfticker.option_chain(expiry).calls)[
                ["contractSymbol", "strike", "impliedVolatility", "volume"]]
            puts_df = pd.DataFrame(self.yfticker.option_chain(expiry).puts)[
                ["contractSymbol", "strike", "impliedVolatility", "volume"]]

            calls_dfs.append(calls_df)
            puts_dfs.append(puts_df)

        df_calls = pd.concat(calls_dfs, ignore_index=True).dropna()
        df_puts = pd.concat(puts_dfs, ignore_index=True).dropna()

        df_calls["maturity"] = df_calls["contractSymbol"].apply(self.get_maturity)
        df_puts["maturity"] = df_puts["contractSymbol"].apply(self.get_maturity)

        # Risk-free rate column
        df_calls["riskFreeRate"] = df_calls["maturity"].apply(self.rate_interpolator())
        df_puts["riskFreeRate"] = df_puts["maturity"].apply(self.rate_interpolator())

        # Forward moneyness
        df_calls["forwardMoneyness"] = np.log(df_calls["strike"] / (
            current_price * np.exp((df_calls["riskFreeRate"] - q) * df_calls["maturity"])
        ))

        df_puts["forwardMoneyness"] = np.log(df_puts["strike"] / (
            current_price * np.exp((df_puts["riskFreeRate"] - q) * df_puts["maturity"])
        ))

        # Total variance
        df_calls["totalVariance"] = (df_calls["impliedVolatility"] ** 2) * df_calls["maturity"]
        df_puts["totalVariance"] = (df_puts["impliedVolatility"] ** 2) * df_puts["maturity"]

        # Filter by moneyness
        df_calls = df_calls.loc[np.abs(df_calls["forwardMoneyness"]) < moneyness]
        df_puts = df_puts.loc[np.abs(df_puts["forwardMoneyness"]) < moneyness]

        df_calls.reset_index(drop=True, inplace=True)
        df_puts.reset_index(drop=True, inplace=True)

        return df_calls, df_puts




if __name__ == "__main__":

    data = yfDataLoader("SPY")
    calls, puts = data.get_option_chain()
    print(calls, puts)


