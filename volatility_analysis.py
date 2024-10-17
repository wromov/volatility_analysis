from data_handler import DataHandler
from volatility_calculator import VolatilityCalculator
from visualizer import Visualizer
from datetime import datetime, timedelta, date

iv_date = date.today() #- timedelta(days=4)# Example date, adjust as needed

# Initialize DataHandler and Visualizer
data_handler = DataHandler()
visualizer = Visualizer()

# Load tickers
tickers = data_handler.load_tickers()
if tickers is None:
    exit()

# Set the folder paths directly to the absolute paths
daily_folder_path = "D:/Scripts/IBKR/daily-bars"
options_data_folder_path = "D:/Scripts/IBKR/options-data"

# Initialize VolatilityCalculator
vol_calculator = VolatilityCalculator(data_handler, visualizer)

# Process all tickers to calculate close-close realized volatility
close_close_df = vol_calculator.process_close_close_vol(tickers, daily_folder_path)
print(close_close_df)

# Process all tickers to calculate GKYZ realized volatility
gkyz_df = vol_calculator.process_gkyz_vol(tickers, daily_folder_path)
print(gkyz_df)

# # Trim DataFrames
# gkyz_df_filtered = gkyz_df.iloc[5:-1]
# close_close_df_filtered = close_close_df.iloc[5:-1]

# Process all tickers to calculate implied volatility for a given date
implied_vol = vol_calculator.process_implied_vol(tickers, options_data_folder_path, iv_date)

# Calculate relative differences
relative_diff_gkyz_df, relative_diff_close_close_df = vol_calculator.calculate_relative_differences(
    gkyz_df, close_close_df, implied_vol
)

# Combine the two relative difference DataFrames using a weighted average
weight_gkyz = 0.6
weight_close_close = 0.4
combined_relative_diff = (weight_gkyz * relative_diff_gkyz_df) + (weight_close_close * relative_diff_close_close_df)

# Set thresholds for filtering large relative differences
threshold_plus = 0.75  # For large positive differences
threshold_neg = -0.5   # For large negative differences

# Create masks for values exceeding the thresholds
mask_positive = combined_relative_diff >= threshold_plus
mask_negative = combined_relative_diff <= threshold_neg

# --- Count occurrences above the threshold for each stock ---

# For positive differences, count how many times each stock exceeds the threshold
positive_counts = mask_positive.sum(axis=0)  # Sum along the time horizon axis for each stock

# For negative differences, count how many times each stock is below the negative threshold
negative_counts = mask_negative.sum(axis=0)  # Sum along the time horizon axis for each stock

# --- Select top N stocks with the most occurrences above/below the threshold ---

top_n = 20

# Select the top stocks with the most positive occurrences
top_positive_stocks = positive_counts.sort_values(ascending=False).head(top_n).index

# Select the top stocks with the most negative occurrences
top_negative_stocks = negative_counts.sort_values(ascending=False).head(top_n).index

# Visualize the relative differences with count overlays
visualizer.visualize_top_relative_differences(combined_relative_diff)

print("done")
