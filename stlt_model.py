import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.metrics import mean_squared_error

data_folder = "cleaned_data/"
csv_files = ["m_S&P500.csv", "m_Gold.csv", "m_WTI.csv", "m_USD.csv", "m_10y-treasury.csv", "m_경제심리지수.csv", "m_Kospi200.csv"]     # "m_KOSDAQ150.csv", 

asset_list = []

# Loop through each CSV file and read it into a DataFrame
for file in csv_files:

    # Read file
    df = pd.read_csv(data_folder+file)

    # Convert the 'Date' column to datetime format
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort the DataFrame by the 'Date' column
    sorted_df = df.sort_values(by='Date')

    # Select a date range
    start_date = '2005-02-01'
    end_date = '2022-12-29'


    date_range = pd.date_range(start_date, end_date, freq='D')
    date_range_df = pd.DataFrame({'Date': date_range})

    # Perform a left join to fill missing dates with None (or NaN for numerical columns)
    fill_empty_rows = pd.merge(date_range_df, sorted_df, on='Date', how='left')

    # Replace NaN values with None for non-numerical columns if needed
    fill_empty_rows.loc[fill_empty_rows['Close'].isna(), 'Close'] = np.nan

    replace_na_rows = fill_empty_rows.fillna(method='ffill')
    replace_na_rows = fill_empty_rows.fillna(method='bfill')
    replace_na_rows = fill_empty_rows.fillna(method='ffill')

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

print("data")
print(result)




X = result[['S&P500', 'Gold', 'WTI', 'USD']]   # , '10y-treasury', , '경제심리지수', 'Kospi200', 
treasury = result[['10y-treasury']]

X_lag_10 = X.shift(10)
X_diff_10 = (X - X_lag_10) / X_lag_10

X_lag_20 = X.shift(20)
X_diff_20 = (X - X_lag_20) / X_lag_20

X_lag_30 = X.shift(30)
X_diff_30 = (X - X_lag_30) / X_lag_30

X_lag_60 = X.shift(60)
X_diff_60 = (X - X_lag_60) / X_lag_60

X_lag_90 = X.shift(90)
X_diff_90 = (X - X_lag_90) / X_lag_90


X_diff = pd.concat([X_diff_10, X_diff_20, X_diff_30, X_diff_60, X_diff_90, treasury], axis=1)
print("X_diff")
print(X_diff)


y_label_asset = 'S&P500'

y_diff_1 = result[y_label_asset].shift(-30) / result[y_label_asset] - 1
y_diff_2 = result[y_label_asset].shift(-25) / result[y_label_asset] - 1
y_diff_3 = result[y_label_asset].shift(-35) / result[y_label_asset] - 1

y_diff = (y_diff_1 + y_diff_2 + y_diff_3) / 3

print("Y_diff")
print(y_diff)



X = X_diff.iloc[90:-35].reset_index(drop=True)
y = y_diff.iloc[90:-35].reset_index(drop=True)

print("X")
print(X)
print("y")
print(y)



# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, shuffle=False)


# Convert the training and testing data to PyTorch tensors
X_train_t = torch.tensor(X_train.values.astype(np.float32))
y_train_t = torch.tensor(y_train.values.astype(np.float32)).view(-1, 1)
X_test_t = torch.tensor(X_test.values.astype(np.float32))
y_test_t = torch.tensor(y_test.values.astype(np.float32)).view(-1, 1)

# Define the neural network model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(X_train_t.shape[1], 128)
        self.fc2 = nn.Linear(128, 1)

        # self.fc3 = nn.Linear(64, 1)
        
        # self.relu = nn.ReLU()
        # self.sigmoid = nn.Sigmoid()

        self.tanh = nn.Tanh()


    def forward(self, x):
        x = self.tanh(self.fc1(x))
        x = self.fc2(x)
        return x

# Create an instance of the model
model = Net()


# define the loss function with L1 regularization
criterion = nn.MSELoss()
l1_lambda = 0.001  # L1 regularization strength


# define the optimizer
optimizer = optim.Adam(model.parameters(), lr=0.00001, weight_decay=0.01)


# Train the model on the training data
tolerance = 10
best_mse = float('inf')
no_improvement_count = 0

from torch.utils.data import DataLoader, TensorDataset


batch_size = 8
train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=batch_size, shuffle=False)

num_epochs = 500

for epoch in range(num_epochs):
    running_loss = 0.0
    for batch_X, batch_y in train_loader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)

        l1_norm = sum([torch.sum(torch.abs(param)) for param in model.fc1.weight])
        loss += l1_lambda * l1_norm  # add L1 regularization term

        loss.backward()
        optimizer.step()
        running_loss += loss.item() * batch_X.size(0) # multiply by batch size

    # Evaluate the model on the testing data
    y_pred_t = model(X_test_t)
    mse = mean_squared_error(y_pred_t.detach().numpy(), y_test_t.detach().numpy())
    print('Epoch [%d], Train Loss: %.8f, Test Loss: %.8f' % (epoch+1, running_loss/X_train_t.shape[0], mse))

    # Check for early stopping
    if mse < best_mse:
        best_mse = mse
        no_improvement_count = 0
        best_model_state = model.state_dict()
    else:
        no_improvement_count += 1
        if no_improvement_count >= tolerance:
            print('Early stopping after epoch %d' % epoch)
            break


# Save the best model state to a file
torch.save(best_model_state, 'best_model_state.pth')

# Load the best model state from a file (for example)
best_model_state = torch.load('best_model_state.pth')
model.load_state_dict(best_model_state)


# Evaluate the model on the testing data
y_pred_t = model(X_test_t)

print('X_test :\n', X_test)
print('y_test :\n', y_test)


# Evaluation metric: accuracy
def evaluate_accuracy(y_true, y_pred):
    y_true_labels = (y_true.detach().numpy() >= 0)
    y_pred_labels = (y_pred.detach().numpy() >= 0)
    return np.mean(y_true_labels == y_pred_labels)


criterion = nn.L1Loss()     # mean absolute error
mae = criterion(y_pred_t, y_test_t)
print('Mean Absolute Error:', mae.item())

accuracy = evaluate_accuracy(y_test_t, y_pred_t)
print("Accuracy : ", accuracy)





fig, ax = plt.subplots(figsize=(12, 8))

plt.plot(y_pred_t.detach().numpy(), y_test)

# Draw a line at x=0 and y=0
plt.axhline(y=0, color='gray', linestyle='--')
plt.axvline(x=0, color='gray', linestyle='--')

plt.xlabel('Prediction')
plt.ylabel('Real')
plt.title('Prediction vs Real')


# Create the figure and axis objects
fig2, ax1 = plt.subplots()

# Plot the first dataset with the first y-axis
color = 'tab:red'
ax1.set_ylabel('Prediction', color=color)
ax1.plot(list(y_pred_t.detach().numpy()), color=color)
ax1.tick_params(axis='y', labelcolor=color)
# ax1.axhline(y=0, color=color, linestyle='--')

# Create a second y-axis for the second dataset
ax2 = ax1.twinx()

# Plot the second dataset with the second y-axis
color = 'tab:blue'
ax2.set_ylabel('Real', color=color)
ax2.plot(list(y_test), color=color)
ax2.tick_params(axis='y', labelcolor=color)
ax2.axhline(y=0, color=color, linestyle='--')

# Add a title and legend
plt.title('Two related datasets with different volatility')

plt.show()