from data_handler import DataHandler
from visualizer import Visualizer
import pandas as pd
import numpy as np

class VolatilityCalculator:
    def __init__(self, data_handler, visualizer):
        self.data_handler = data_handler
        self.visualizer = visualizer
        self.final_close_close_rv = {}
        self.final_gkyz_rv = {}
        self.final_iv = {}

    def calculate_realized_volatility(self, df, stock_symbol, start_date, end_date, F=1):
        """Calculate the close-to-close realized volatility for a specified date range."""
        # Ensure the index is a DatetimeIndex for date filtering
        df.index = pd.to_datetime(df.index)
        
        # Filter data for the specified stock and date range
        data = df[(df['Symbol'] == stock_symbol) & (df.index >= start_date) & (df.index <= end_date)].copy()
        
        # Calculate log returns
        data['Log Returns'] = np.log(data['Close'] / data['Close'].shift(1))
        data = data.apply(pd.to_numeric, errors='coerce')
        
        # Drop the first NA value created by the shift operation
        data = data.dropna(subset=['Log Returns'])
        
        # Calculate the number of observations
        N = len(data['Log Returns'])
        
        if N < 2:
            return np.nan  # Not enough data to calculate volatility
        
        # Calculate the sum of squared log returns
        squared_data = data['Log Returns'] ** 2
        sum_squared_log_returns = squared_data.sum(axis=0)
        
        # Calculate the sample variance and adjust for population variance
        sample_variance = np.sqrt((sum_squared_log_returns) / N)
        population_variance = sample_variance * (N / (N - 1))

        # Calculate the realized volatility
        realized_volatility = population_variance * np.sqrt(252)
        
        return realized_volatility
    
    def get_close_close_vol(self, df, stock_symbol):
        """Calculate the close-close realized volatility for a given ticker."""
        end_date = df.index[-1]  # Last available date in the DataFrame
        date_ranges = {
            # "5 year": end_date - pd.offsets.BDay(5*252),
            "1 year": end_date - pd.offsets.BDay(252),  # Approximate number of business days in a year
            "9 month": end_date - pd.offsets.BDay(189),  # Approximate number of business days in 9 months
            "6 month": end_date - pd.offsets.BDay(126),  # Approximate number of business days in 6 months
            "3 month": end_date - pd.offsets.BDay(63),  # Approximate number of business days in 3 months
            "1 month": end_date - pd.offsets.BDay(21),  # Approximate number of business days in a month
            "2 week": end_date - pd.offsets.BDay(10),
            "1 week": end_date - pd.offsets.BDay(5),  # Approximate number of business days in a week
            # "2 day": end_date - pd.offsets.BDay(2),
        }
        
        close_close_rv = {}
        for period, start_date in date_ranges.items():
            if start_date < df.index[0]:  # Ensure the start date is within the available data range
                close_close_rv[period] = None
            else:
                close_close_rv[period] = self.calculate_realized_volatility(df, stock_symbol, start_date, end_date)
            
        return close_close_rv
    
    def process_close_close_vol(self, tickers, daily_folder_path):
        """Loop through each ticker to calculate close-close realized volatility."""
        for ticker in tickers:
            print(f"Processing {ticker} - Close Close RV")
            df = self.data_handler.load_parquet_file(daily_folder_path, ticker)
            if df is not None:
                results = self.get_close_close_vol(df, ticker)
                self.final_close_close_rv[ticker] = results

        # Convert final dictionary to DataFrame
        close_close_df = pd.DataFrame.from_dict(self.final_close_close_rv, orient='index').T
        return close_close_df

    def calculate_rolling_gkyz_volatility(self, df, stock_symbol, window, F=252, start_date=None, end_date=None):
        """Calculate rolling GKYZ realized volatility for a given stock and window size."""
        # Ensure the index is a DatetimeIndex for date filtering
        df.index = pd.to_datetime(df.index)

        # Filter data for the specified stock
        data = df[df['Symbol'] == stock_symbol].copy()

        # Apply date filtering if start_date and end_date are provided
        if start_date is not None:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date is not None:
            data = data[data.index <= pd.to_datetime(end_date)]

        # Ensure we have all necessary columns
        if not {'Open', 'High', 'Low', 'Close'}.issubset(data.columns):
            raise ValueError("Missing required data columns.")

        # Logarithmic returns
        data['log_oc_prev'] = np.log(data['Open'] / data['Close'].shift(1))
        data['log_hl'] = np.log(data['High'] / data['Low'])
        data['log_co'] = np.log(data['Close'] / data['Open'])

        # Calculation of GKYZ components
        data['term1'] = data['log_oc_prev'] ** 2
        data['term2'] = 0.5 * (data['log_hl'] ** 2)
        data['term3'] = (2 * np.log(2) - 1) * (data['log_co'] ** 2)

        # Rolling window calculation of variance
        data['variance'] = data['term1'] + data['term2'] - data['term3']
        rolling_variance = data['variance'].rolling(window=window).sum()

        # Calculate rolling GKYZ realized volatility
        gkyz_scaling_factor = np.sqrt(F * 252 / window)
        data['rolling_gkyz_volatility'] = gkyz_scaling_factor * np.sqrt(rolling_variance)

        # Return the data with Close and rolling_gkyz_volatility columns
        return data[['Close', 'rolling_gkyz_volatility']]

    def get_gkyz_vol(self, df, stock_symbol):
        """Get rolling GKYZ realized volatility for different date ranges."""
        date_ranges = {
            # "5 year": 5 * 252,
            "1 year": 252,  # Approximate number of business days in a year
            "9 month": 189,  # Approximate number of business days in 9 months
            "6 month": 126,  # Approximate number of business days in 6 months
            "3 month": 63,  # Approximate number of business days in 3 months
            "1 month": 21,  # Approximate number of business days in a month
            "2 week": 10,
            "1 week": 5,  # Approximate number of business days in a week
            # "2 day": 2,
        }

        gkyz_rv = {}
        F = 1

        for period, window_size in date_ranges.items():
            volatility_data = self.calculate_rolling_gkyz_volatility(df, stock_symbol, window_size, F)
            if not volatility_data.empty:
                last_valid_volatility = (
                    volatility_data['rolling_gkyz_volatility']
                    .dropna()
                    .iloc[-1]
                    if not volatility_data['rolling_gkyz_volatility'].dropna().empty
                    else np.nan
                )
                gkyz_rv[period] = last_valid_volatility
            else:
                gkyz_rv[period] = np.nan

        return gkyz_rv

    def process_gkyz_vol(self, tickers, daily_folder_path):
        """Loop through each ticker to calculate GKYZ realized volatility."""
        for ticker in tickers:
            print(f"Processing {ticker} - GKYZ RV")
            df = self.data_handler.load_parquet_file(daily_folder_path, ticker)
            if df is not None:
                results = self.get_gkyz_vol(df, ticker)
                self.final_gkyz_rv[ticker] = results

        # Convert final dictionary to DataFrame
        gkyz_df = pd.DataFrame.from_dict(self.final_gkyz_rv, orient='index').T
        return gkyz_df
    
    def process_implied_vol(self, tickers, options_data_folder_path, iv_date):
        """Loop through each ticker to calculate implied volatility for a given date."""
        for ticker in tickers:
            print(f"Processing {ticker} - Implied Volatility")

            # Load options data parquet file
            options_file_path = f"{options_data_folder_path}/{ticker}.parquet"
            try:
                df = pd.read_parquet(options_file_path)
            except FileNotFoundError:
                print(f"Options data file for {ticker} not found: {options_file_path}")
                continue
            except Exception as e:
                print(f"Error loading options data for {ticker}: {e}")
                continue

            # Filter the data to only keep data on the specific date (iv_date)
            df['time'] = pd.to_datetime(df['time'])
            filtered_df = df[df['time'].dt.date == pd.to_datetime(iv_date).date()].copy()

            if filtered_df.empty:
                print(f"No data available for {ticker} on {iv_date}")
                continue

            # Calculate average implied volatility by grouping by 'lastTradeDateOrContractMonth'
            filtered_df = filtered_df.reset_index(drop=True)
            grouped_df = filtered_df.groupby('lastTradeDateOrContractMonth').mean(numeric_only=True).reset_index()
            maturity_iv = grouped_df[['lastTradeDateOrContractMonth', 'lastGreeks_iv', 'bidGreeks_iv', 'askGreeks_iv', 'modelGreeks_iv']]
            
            # Drop the first row to remove contracts without data
            maturity_iv = maturity_iv.drop(0)

            # Calculate the average model implied volatility
            average_iv = maturity_iv.mean(numeric_only=True)
            self.final_iv[ticker] = average_iv.modelGreeks_iv

        # Convert the final dictionary to a pandas Series
        implied_vol = pd.Series(self.final_iv)
        return implied_vol

    def calculate_relative_differences(self, gkyz_df_filtered, close_close_df_filtered, implied_vol):
        """Calculate relative differences between implied volatility and realized volatilities."""
        # Check if the DataFrames are empty
        if gkyz_df_filtered.empty or close_close_df_filtered.empty:
            print("One or both of the filtered DataFrames are empty. Skipping calculation.")
            return pd.DataFrame(), pd.DataFrame()

        # Convert gkyz_df and close_close_df from DataFrames to NumPy arrays for faster calculations
        gkyz_array = gkyz_df_filtered.to_numpy()  # Shape: (number of tenors, number of stocks)
        close_close_array = close_close_df_filtered.to_numpy()  # Same shape as above

        # Align the implied_vol DataFrame to match the columns in gkyz_df and close_close_df
        # Assume implied_vol is a pandas Series with the same index as gkyz_df columns
        implied_vol_array = np.array(implied_vol)  # Shape: (number of stocks,)

        # Expand implied_vol_array to match the shape of gkyz_array and close_close_array
        implied_vol_expanded = np.tile(implied_vol_array, (gkyz_array.shape[0], 1))  # Broadcast IV across rows

        # Calculate the relative difference for GKYZ and Close-Close Historical Volatility
        try:
            relative_diff_gkyz = (implied_vol_expanded - gkyz_array) / gkyz_array
            relative_diff_close_close = (implied_vol_expanded - close_close_array) / close_close_array
        except ValueError as e:
            print(f"ValueError encountered during calculation: {e}")
            return pd.DataFrame(), pd.DataFrame()

        # Convert the results back to DataFrames for better readability and further analysis
        relative_diff_gkyz_df = pd.DataFrame(relative_diff_gkyz, index=gkyz_df_filtered.index, columns=gkyz_df_filtered.columns)
        relative_diff_close_close_df = pd.DataFrame(relative_diff_close_close, index=close_close_df_filtered.index, columns=close_close_df_filtered.columns)

        return relative_diff_gkyz_df, relative_diff_close_close_df
