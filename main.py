import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt

# Function to get data from FRED (Federal Reserve Economic Data)
def get_fred_data(series, start, end):
    try:
        data = pdr.get_data_fred(series, start, end)
        return data
    except Exception as e:
        print(f"Data download error: {e}")
        return None

# Function to calculate real return adjusted for inflation
def calculate_real_return(nominal_return, inflation_rate):
    real_return = (1 + nominal_return) / (1 + inflation_rate) - 1
    return real_return

# Function to calculate nominal and real returns and final investment value
def calculate_returns(ticker, initial_investment, start_date, end_date, inflation_rate, interest_rate):
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
    except Exception as e:
        print(f"Data download error: {e}")
        return None, None, None

    if data.empty or len(data) < 2:
        print(f"Insufficient data found: {ticker}")
        return None, None, None

    initial_price = data['Close'].iloc[0]
    final_price = data['Close'].iloc[-1]

    total_return = (final_price - initial_price) / initial_price

    # Calculate investment duration in years
    years = (end_date - start_date).days / 365.25

    annual_return = (1 + total_return) ** (1/years) - 1

    real_annual_return = calculate_real_return(annual_return, inflation_rate)
    
    # Convert real_annual_return to scalar before applying it in a formula
    if isinstance(real_annual_return, pd.Series):
        real_annual_return = real_annual_return.iloc[0]

    final_value = initial_investment * (1 + real_annual_return) ** years

    return total_return, real_annual_return, final_value

def main():
    initial_investment_tl = float(input("Enter initial investment amount in TRY: "))
    
    # Get time frame input
    start_date_str = input("Enter start date (YYYY-MM-DD): ")
    end_date_str = input("Enter end date (YYYY-MM-DD): ")

    # Convert to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Get USD/TRY exchange rate for the investment period
    try:
        usdtry = yf.download("USDTRY=X", start=start_date, end=end_date)
    except Exception as e:
        print(f"USD/TRY data download error: {e}")
        return

    if usdtry.empty or len(usdtry) < 2:
        print("Insufficient USD/TRY data found")
        return

    initial_usd_rate = usdtry['Close'].iloc[0]
    final_usd_rate = usdtry['Close'].iloc[-1]

    # Convert initial investment from TRY to USD
    initial_investment_usd = initial_investment_tl / initial_usd_rate

    # Get inflation and interest rate data for Turkey and the US
    turkish_inflation = get_fred_data('TURCPIALLMINMEI', start_date, end_date)
    us_inflation = get_fred_data('CPIAUCSL', start_date, end_date)
    turkish_interest_rate = get_fred_data('IR3TIB01TRM156N', start_date, end_date)
    us_interest_rate = get_fred_data('FEDFUNDS', start_date, end_date)

    if any(data is None for data in [turkish_inflation, us_inflation, turkish_interest_rate, us_interest_rate]):
        print("Unable to fetch inflation and/or interest rate data")
        return

    # Calculate the average inflation and interest rates
    turkish_inflation = turkish_inflation.pct_change().mean() * 12
    us_inflation = us_inflation.pct_change().mean() * 12
    turkish_interest_rate = turkish_interest_rate.mean() / 100
    us_interest_rate = us_interest_rate.mean() / 100

    # Calculate real returns for BIST100 and S&P500
    bist_return, bist_real_annual, bist_final_usd = calculate_returns(
        "XU100.IS", initial_investment_usd, start_date, end_date, turkish_inflation, turkish_interest_rate
    )

    sp500_return, sp500_real_annual, sp500_final_usd = calculate_returns(
        "^GSPC", initial_investment_usd, start_date, end_date, us_inflation, us_interest_rate
    )

    if bist_return is not None and sp500_return is not None:
        # Convert final values back to TRY
        bist_final_tl = bist_final_usd * final_usd_rate
        sp500_final_tl = sp500_final_usd * final_usd_rate

        # Print the results
        print(f"Initial Investment: {initial_investment_tl:.2f} TL")
        print(f"Initial USD/TRY Rate: {initial_usd_rate:.2f}")
        print(f"Final USD/TRY Rate: {final_usd_rate:.2f}")
        print("\nBIST 100 Results:")
        print(f"Total Nominal Return: %{bist_return * 100:.2f}")
        print(f"Annual Real Return (Inflation Adjusted): %{bist_real_annual * 100:.2f}")
        print(f"Final Value: {bist_final_tl:.2f} TL")
        print("\nS&P 500 Results:")
        print(f"Total Nominal Return: %{sp500_return * 100:.2f}")
        print(f"Annual Real Return (Inflation Adjusted): %{sp500_real_annual * 100:.2f}")
        print(f"Final Value: {sp500_final_tl:.2f} TL")

        # Visualization
        labels = ['BIST 100', 'S&P 500']
        final_values = [bist_final_tl, sp500_final_tl]
        plt.bar(labels, final_values)
        plt.ylabel('Final Value (TRY)')
        plt.title('Comparison of Final Investment Values')
        plt.show()

    else:
        print("An error occurred during the calculations.")

if __name__ == "__main__":
    main()
