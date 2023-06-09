import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data_folder = "cleaned_data/"
csv_files = ["m_S&P500.csv", "m_Gold.csv", "m_Kospi200.csv", "m_USD.csv", "m_WTI.csv", "m_K_treasury.csv", "m_K_corp_bond.csv", "m_global_bonds.csv"]     # "m_KOSDAQ150.csv", 

# csv_files = ["m_Kospi200.csv", "KORLOLITONOSTSAM.csv"] "m_EuroStoxx50.csv", 

asset_list = []

# Loop through each CSV file and read it into a DataFrame
for file in csv_files:

    print(file)

    # Read file
    df = pd.read_csv(data_folder+file)

    # Convert the 'Date' column to datetime format
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort the DataFrame by the 'Date' column
    sorted_df = df.sort_values(by='Date')

    # Select a date range
    start_date = '2001-01-02'
    end_date = '2022-12-29'


    date_range = pd.date_range(start_date, end_date, freq='D')
    date_range_df = pd.DataFrame({'Date': date_range})

    # Perform a left join to fill missing dates with None (or NaN for numerical columns)
    fill_empty_rows = pd.merge(date_range_df, sorted_df, on='Date', how='left')

    # Replace NaN values with None for non-numerical columns if needed
    fill_empty_rows.loc[fill_empty_rows['Close'].isna(), 'Close'] = np.nan

    replace_na_rows = fill_empty_rows.fillna(method='ffill')
    replace_na_rows = fill_empty_rows.fillna(method='bfill')

    # Change the column name
    column_name_rows = replace_na_rows.rename(columns={'Close': file[2:-4]})

    # print(column_name_rows)


    selected_rows = column_name_rows[(column_name_rows['Date'] >= start_date) & (column_name_rows['Date'] <= end_date)]

    # print("\nSelected rows for the date range:")
    # print(selected_rows)

    asset_list.append(column_name_rows)




result = asset_list[0]

for df in asset_list[1:]:
    result = pd.merge(result, df, on='Date', how='inner')

print(result)


# # Set the 'Date' column as the index
# result.set_index('Date', inplace=True)

# returns = result.pct_change()



# # Calculate covariance of returns
# cov_matrix = returns.cov()

# # ["m_S&P500.csv", "m_Gold.csv", "m_Kospi200.csv", "m_USD.csv", "m_WTI.csv", "m_K_treasury.csv", "m_K_corp_bond.csv", "m_global_bonds.csv"]
# weights = np.array([0.20, 0.14, 0.14, 0.05, 0.01, 0.15, 0.15, 0.10])

# # Calculate portfolio variance
# port_variance = np.dot(weights.T, np.dot(cov_matrix, weights))

# # Calculate portfolio volatility (standard deviation)
# port_volatility = np.sqrt(port_variance)

# print(f"The portfolio's risk (volatility) is: {port_volatility}")

# exit()






# Compute the correlation between the columns
correlation = result.corr()

# Display the correlation results
print("Correlation between columns:")
print(correlation)

# Save the correlation matrix as an Excel file
correlation.to_excel('correlation_matrix.xlsx')





# Set the 'Date' column as the index
result.set_index('Date', inplace=True)

normalized_df = result.divide(result.iloc[0])
# print(normalized_df)

# Plot the data
fig, ax = plt.subplots(figsize=(12, 8))

for asset in normalized_df.columns:
    plt.plot(normalized_df[asset], label=asset)


plt.xlabel('Date')
plt.ylabel('Value')
plt.title('Time Series Plot of Various Financial Indices')
plt.legend(loc='best')

plt.show()








# Calculate daily returns
daily_returns = result.pct_change()

# Calculate the volatility (standard deviation of daily returns)
volatility = daily_returns.std()

print("\nVolatility:\n", volatility)

