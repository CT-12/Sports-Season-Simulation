import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 讀取資料
df = pd.read_csv('pitching_clean2000.csv')

features = ['W', 'L', 'ERA', 'IP', 'H',
            'AVG', 'R', 'ER', 'BB','SO', 'WHIP', 'WAR']
target = 'WAR_next'

X = df[features].copy()
y = df[target].copy()

# 時間切分
train_idx = df['Season'] < 2023
val_idx   = df['Season'] == 2023
test_idx  = df['Season'] == 2024


X_train, X_val, X_test = X[train_idx].copy(), X[val_idx].copy(), X[test_idx].copy()
y_train, y_val, y_test = y[train_idx].copy(), y[val_idx].copy(), y[test_idx].copy()

X_train_np = np.ascontiguousarray(X_train)
y_train_np = np.ascontiguousarray(y_train)
X_val_np = np.ascontiguousarray(X_val)
y_val_np = np.ascontiguousarray(y_val)
X_test_np = np.ascontiguousarray(X_test)
y_test_np = np.ascontiguousarray(y_test)

print("Data loaded and converted to contiguous NumPy arrays!")

# 標準化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_np)
X_val_scaled   = scaler.transform(X_val_np)
X_test_scaled  = scaler.transform(X_test_np)

# 訓練 Ridge 模型
# alpha 是 L2 正則化參數
ridge_model = Ridge(alpha=1.0, random_state=42)
ridge_model.fit(X_train_scaled, y_train_np)

# 驗證集預測
y_val_pred = ridge_model.predict(X_val_scaled)
mae_val = mean_absolute_error(y_val_np, y_val_pred)
rmse_val = np.sqrt(mean_squared_error(y_val_np, y_val_pred))
r2_val = r2_score(y_val_np, y_val_pred)

print("\n=== 驗證集評估指標 (Ridge) ===")
print("MAE :", mae_val)
print("RMSE:", rmse_val)
print("R² :", r2_val)

# 測試集預測
y_test_pred = ridge_model.predict(X_test_scaled)
mae_test = mean_absolute_error(y_test_np, y_test_pred)
rmse_test = np.sqrt(mean_squared_error(y_test_np, y_test_pred))
r2_test = r2_score(y_test_np, y_test_pred)

print("\n=== 測試集評估指標 (Ridge) ===")
print("MAE :", mae_test)
print("RMSE:", rmse_test)
print("R² :", r2_test)

# 輸出模型係數
coef_df = pd.DataFrame({
    'Feature': features,
    'Coefficient': ridge_model.coef_
})
coef_df = coef_df.sort_values(by='Coefficient', ascending=False).reset_index(drop=True)

print("\n=== Ridge 迴歸係數 ===")
print(coef_df)

# === 用 2025 的數據預測 2026 WAR 並輸出 CSV ===

# 再次讀取 players_hitting.csv
df_hitting = pd.read_csv('players_pitching.csv')
df_2025 = df_hitting[df_hitting['Season'] == 2025].copy()

if len(df_2025) == 0:
    raise ValueError("資料中沒有 2025 年的紀錄，無法預測 2026 WAR！")

X_2025 = df_2025[features].copy()

X_2025_np = np.ascontiguousarray(X_2025)

# 對 2025 資料進行標準化
X_2025_scaled = scaler.transform(X_2025_np)

df_2025['WAR_pred_2026'] = ridge_model.predict(X_2025_scaled)

output_cols = ['IDfg', 'Name', 'Season', 'WAR', 'WAR_pred_2026']
df_2026_pred = df_2025[output_cols].copy()

# 儲存 CSV
df_2026_pred.to_csv("predicted(p)_WAR_2026_Ridge.csv", index=False)

print("\n2026 WAR 預測已輸出至 predicted_WAR_2026_Ridge.csv !")
