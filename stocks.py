import warnings
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from statsmodels.tsa.vector_ar.vecm import VECM, select_order, select_coint_rank
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.stattools import adfuller
from stock_report import generate_report

# Add warning filters before your analysis
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
# Specifically for yfinance warnings
warnings.filterwarnings(
    "ignore", message="The behavior of DatetimeProperties.to_pydatetime is deprecated"
)
# For statsmodels convergence warnings
warnings.filterwarnings(
    "ignore", message="Maximum Likelihood optimization failed to converge"
)


def download_stock_data(ticker, start_date, end_date, retries=3):
    """Download stock data with error handling and retries"""
    for attempt in range(retries):
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            if not data.empty:
                return data
        except Exception as e:
            if attempt == retries - 1:
                raise Exception(f"Failed to download {ticker} data: {str(e)}")
            continue
    return None


# Ensure end date is not in the future and handle market closure days
end_date = min(
    datetime.now(), datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
)
start_date = datetime(2024, 1, 1)

# For specific code blocks that might raise warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    # Your code that generates warnings here
    apple_stocks = download_stock_data(["AAPL"], start_date, end_date)
    meta_stocks = download_stock_data(["META"], start_date, end_date)

# Combine adjusted closing prices into a single DataFrame
data = pd.DataFrame(
    {
        "Apple": apple_stocks["Adj Close"].squeeze(),
        "Meta": meta_stocks["Adj Close"].squeeze(),
    }
)

# Drop rows with missing values and verify sufficient data
data.dropna(inplace=True)
if len(data) < 30:  # Minimum required for meaningful analysis
    raise ValueError("Insufficient data points for analysis")


def adf_test(series, name):
    """Enhanced ADF test with clear interpretation"""
    result = adfuller(series)
    print(f"ADF Test for {name}:")
    print(f"ADF Statistic: {result[0]:.4f}")
    print(f"p-value: {result[1]:.4f}")
    print("Critical Values:")
    for key, value in result[4].items():
        print(f"\t{key}: {value:.4f}")
    is_stationary = result[1] < 0.05
    print(f"Series is {'stationary' if is_stationary else 'non-stationary'}")
    print("\n")
    return result[1]


# Perform stationarity tests
apple_adf = adf_test(data["Apple"], "Apple")
meta_adf = adf_test(data["Meta"], "Meta")

# Test for cointegration with error handling
try:
    data_combined = data[["Apple", "Meta"]]
    rank_test = select_coint_rank(data_combined, det_order=0, k_ar_diff=1)
    print("Cointegration Rank:", rank_test.rank)

    # Fit VECM with optimal lag order
    lag_order = select_order(data_combined, maxlags=min(15, len(data) // 5))
    print("Optimal Lag Order:", lag_order.selected_orders)

    vecm = VECM(data_combined, k_ar_diff=lag_order.aic, coint_rank=rank_test.rank)
    vecm_fit = vecm.fit()
    print(vecm_fit.summary())

    # Enhanced visualization
    plt.figure(figsize=(12, 8))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot original series
    ax1.plot(data_combined.index, data_combined["Apple"], label="Apple")
    ax1.plot(data_combined.index, data_combined["Meta"], label="Meta")
    ax1.set_title("Original Price Series")
    ax1.legend()

    # Plot residuals
    residuals = vecm_fit.resid
    sns.lineplot(data=residuals, ax=ax2)
    ax2.set_title("VECM Model Residuals")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Residual Value")

    plt.tight_layout()
    plt.show()

    # Save results
    results = {
        "cointegration_rank": rank_test.rank,
        "optimal_lag": lag_order.aic,
        "apple_adf_pvalue": apple_adf,
        "meta_adf_pvalue": meta_adf,
        "model_summary": vecm_fit.summary(),
    }

    # Optional: Save results to file
    with open("vecm_results.txt", "w") as f:
        f.write(str(results))

    report_file = generate_report(
        data, apple_adf, meta_adf, rank_test, lag_order, vecm_fit, residuals
    )
    print(f"Report generated: {report_file}")

except Exception as e:
    print(f"Error in VECM analysis: {str(e)}")
