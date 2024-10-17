import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

class Visualizer:
    def visualize_top_relative_differences(self, combined_relative_diff, N=20):
        """Visualize the top N highest and lowest relative differences between implied volatility and realized volatilities, with caps on relative values."""

        # Step 1: Apply cap on the relative values to filter out potential outliers
        capped_diff = combined_relative_diff[(combined_relative_diff <= 2) & (combined_relative_diff >= -1.75)]

        # Step 2: Identify Top N Positive and Top N Negative Stocks
        # Flatten the DataFrame to get a long format for sorting
        combined_long = capped_diff.stack().reset_index()
        combined_long.columns = ['Time Horizon', 'Stock', 'Relative Difference']

        # Sort by relative difference to get the top N highest and lowest values
        top_n_highest = combined_long.nlargest(N, 'Relative Difference')
        top_n_lowest = combined_long.nsmallest(N, 'Relative Difference')

        # Debugging: Print the top N highest and lowest values
        print(f"Top {N} Highest Relative Differences:")
        print(top_n_highest)
        print(f"Top {N} Lowest Relative Differences:")
        print(top_n_lowest)

        # Extract the unique stocks from the top N highest and lowest relative differences
        top_positive_stocks = top_n_highest['Stock'].unique()
        top_negative_stocks = top_n_lowest['Stock'].unique()

        # Step 3: Filter Original Data for Selected Stocks and Time Horizons
        # Create filtered DataFrames for the top N positive and negative values
        top_positive_df = combined_relative_diff.loc[:, top_positive_stocks]
        top_negative_df = combined_relative_diff.loc[:, top_negative_stocks]

        # Ensure the order of time horizons matches the original DataFrame
        time_horizon_order = combined_relative_diff.index

        # Plot Heatmap for Top N Positive Stocks
        if not top_positive_df.empty:
            plt.figure(figsize=(12, 10))
            ax = sns.heatmap(
                top_positive_df.loc[time_horizon_order],
                cmap="coolwarm",
                center=0,
                annot=top_positive_df.loc[time_horizon_order],
                fmt=".2f",
                annot_kws={"size": 10},
                vmax=2,
                vmin=-2
            )
            plt.xticks(rotation=45, ha='right', fontsize=10)
            plt.yticks(rotation=0, fontsize=10)
            plt.title(f"Top {N} Stocks with Highest Relative Differences", fontsize=14)
            plt.xlabel("Stocks", fontsize=12)
            plt.ylabel("Time Horizons", fontsize=12)
            plt.tight_layout()
            plt.show()
        else:
            print(f"No data to plot for top {N} highest relative differences.")

        # Plot Heatmap for Top N Negative Stocks
        if not top_negative_df.empty:
            plt.figure(figsize=(12, 10))
            ax = sns.heatmap(
                top_negative_df.loc[time_horizon_order],
                cmap="coolwarm",
                center=0,
                annot=top_negative_df.loc[time_horizon_order],
                fmt=".2f",
                annot_kws={"size": 10},
                vmax=2,
                vmin=-2
            )
            plt.xticks(rotation=45, ha='right', fontsize=10)
            plt.yticks(rotation=0, fontsize=10)
            plt.title(f"Top {N} Stocks with Lowest Relative Differences", fontsize=14)
            plt.xlabel("Stocks", fontsize=12)
            plt.ylabel("Time Horizons", fontsize=12)
            plt.tight_layout()
            plt.show()
        else:
            print(f"No data to plot for top {N} lowest relative differences.")
