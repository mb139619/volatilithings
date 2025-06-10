import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from utilities import compute_year_fraction

class yfDataLoader:

    def __init__(self, ticker:str):

        self.ticker = ticker
        self.yfticker = yf.Ticker(self.ticker)


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

        contract_symbol = contract_symbol.removeprefix(self.ticker)
        if contract_symbol[0] =="W":
            contract_symbol = contract_symbol[1:7]
        else: 
            contract_symbol = contract_symbol[:6]
        maturity_date = datetime.strptime(contract_symbol, "%y%m%d")
        maturity = compute_year_fraction(datetime.today(), maturity_date + timedelta(days=1))

        return maturity
            
    def get_option_chain(self, moneyness = 0.3):

        option_expiries = self.yfticker.options
        current_price = self.get_current_price()
        calls_dfs = []
        puts_dfs = []
        
        for expiry in option_expiries:
            calls_df = pd.DataFrame(self.yfticker.option_chain(expiry).calls)[
                ["contractSymbol", "strike", "impliedVolatility", "volume"]]
            puts_df = pd.DataFrame(self.yfticker.option_chain(expiry).puts)[
                ["contractSymbol", "strike", "impliedVolatility", "volume"]]
            
            calls_dfs.append(calls_df)
            puts_dfs.append(puts_df)

        df_calls = pd.concat(calls_dfs, ignore_index=True)
        df_puts = pd.concat(puts_dfs, ignore_index=True)

        df_calls.dropna(inplace=True)
        df_puts.dropna(inplace=True)
        

        df_calls["maturity"] = df_calls["contractSymbol"].apply(self.get_maturity)
        df_puts["maturity"] = df_puts["contractSymbol"].apply(self.get_maturity)
        
        df_calls["forward_moneyness"] = np.log(df_calls["strike"] / current_price)
        df_puts["forward_moneyness"] = np.log(df_puts["strike"] / current_price)
        
        df_calls["total_variance"] = (df_calls["impliedVolatility"] ** 2) * df_calls["maturity"]
        df_puts["total_variance"] = (df_puts["impliedVolatility"] ** 2) * df_puts["maturity"]

        return df_calls, df_puts

    @staticmethod
    def get_risk_free_rate(T):
        
        """
        Return risk-free rate for given maturity T (in years), using US Treasury yield proxies from Yahoo Finance.
        
        For now, we use:
        - ^IRX: 3M T-Bill (~0.25y)
        - ^FVX: 5Y yield (~5y)
        - ^TNX: 10Y yield (~10y)
        
        We interpolate linearly between available points.
        
        Returns rate as decimal (e.g. 0.045 for 4.5%).
        """
        
        # Define tickers and corresponding times (in years)
        yield_data = {
            '^IRX': 0.25,  # 3M T-Bill ~ 0.25 year
            '^FVX': 5.0,   # 5Y yield
            '^TNX': 10.0   # 10Y yield
        }
        
        # Download latest data
        rates = {}
        for ticker, maturity in yield_data.items():
            df = yf.download(ticker, period='5d', interval='1d', progress=False)
            last_valid_close = df['Close'].dropna().iloc[-1]
            # ^IRX is in percent — divide by 100
            rates[maturity] = last_valid_close / 100.0
        
        # Sort maturities
        maturities = np.array(sorted(rates.keys()))
        rate_values = np.array([rates[m] for m in maturities])
        
        # Interpolate
        if T <= maturities[0]:
            r = rate_values[0]
        elif T >= maturities[-1]:
            r = rate_values[-1]
        else:
            r = np.interp(T, maturities, rate_values)
        
        return r



if __name__ == "__main__":

    data = yfDataLoader("SPY")
    calls, puts = data.get_option_chain()

    print(calls, puts)
