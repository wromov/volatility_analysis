import os
import pandas as pd

class DataHandler:
    def __init__(self, base_folder=None):
        self.base_folder = base_folder if base_folder else os.getcwd()

    def get_folder_path(self, folder_name):
        """Get the path to a specific folder inside the base directory."""
        return os.path.join(self.base_folder, folder_name)

    def load_tickers(self, file_name='options-tickers.csv'):
        """Load the tickers from the specified CSV file."""
        tickers_path = os.path.join(self.base_folder, file_name)
        try:
            tickers_df = pd.read_csv(tickers_path)
            return tickers_df['Symbol']
        except FileNotFoundError:
            print(f"Ticker file {file_name} not found in base directory {self.base_folder}.")
            return None

    def load_parquet_file(self, folder_path, ticker):
        """Load a parquet file for the given ticker."""
        file_path = os.path.join(folder_path, f"{ticker}.parquet")
        
        # Print the file path for debugging
        print(f"Attempting to load file from: {file_path}")
        
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        # Load the parquet file
        try:
            df = pd.read_parquet(file_path)
            print(f"Successfully loaded file for ticker: {ticker}")
            return df
        except Exception as e:
            print(f"Error loading file for ticker {ticker}: {e}")
            return None