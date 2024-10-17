# Volatility Analysis #
This repository contains code for analyzing and comparing historical and implied volatility of financial instruments, such as stocks and options. 
The analysis focuses on calculating historical volatility using different methods and comparing it with implied volatility for a deeper understanding of market behavior.

## Overview ##
This project provides tools to:

Calculate historical volatility using multiple methods, including Garman-Klass-Yang-Zhang (GKYZ) and Close-to-Close.
Retrieve and analyze implied volatility data from stock options.
Combine historical and implied volatility data for comparative analysis.
Plot time series data for visual analysis.

The code leverages Python libraries like pandas, matplotlib, and ib_insync for data processing, visualization, and interaction with the Interactive Brokers API for live option data.

## Features ##
-Calculate historical volatility using GKYZ and Close-Close methods.
-Fetch implied volatility from real-time options market data.
-Time series plotting of volatility data.
-Comparison of historical and implied volatility.
-Scriptable for batch processing of multiple stock tickers.
-Customizable analysis based on time frames and expirations.