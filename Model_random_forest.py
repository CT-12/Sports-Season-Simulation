import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 讀取資料
df = pd.read_csv('batting_clean2000.csv')

features = ['AB', 'R', 'H', 'HR', 'RBI',
            'AVG', 'OBP', 'SLG', 'OPS', 'WAR'] 

target = 'WAR_next'

X = df[features]
y = df[target]

# 時間切分訓練/驗證/測試集
train_idx = df['Season'] < 2023
val_idx   = df['Season'] == 2023
test_idx  = df['Season'] == 2024

X_train, X_val, X_test = X[train_idx], X[val_idx], X[test_idx]
y_train, y_val, y_test = y[train_idx], y[val_idx], y[test_idx]

# 建立 Random Forest 模型
rf_model = RandomForestRegressor(
    n_estimators=500,
    max_depth=15,         
    min_samples_leaf=5,    
    random_state=42,
    n_jobs=-1
)

# 訓練模型
rf_model.fit(X_train, y_train)

# 驗證集預測
y_val_pred = rf_model.predict(X_val)
mae_val = mean_absolute_error(y_val, y_val_pred)
rmse_val = np.sqrt(mean_squared_error(y_val, y_val_pred))
r2_val = r2_score(y_val, y_val_pred)

print("=== 驗證集評估指標 ===")
print("MAE :", mae_val)
print("RMSE:", rmse_val)
print("R²  :", r2_val)

# 測試集預測
y_test_pred = rf_model.predict(X_test)
mae_test = mean_absolute_error(y_test, y_test_pred)
rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
r2_test = r2_score(y_test, y_test_pred)

print("=== 測試集評估指標 ===")
print("MAE :", mae_test)
print("RMSE:", rmse_test)
print("R²  :", r2_test)

# 輸出特徵重要度
feat_importances = pd.DataFrame({
    'Feature': features,
    'Importance': rf_model.feature_importances_
}).sort_values(by='Importance', ascending=False)

print("\n=== 特徵重要度 ===")
print(feat_importances)

# === 用 2025 的數據預測 2026 WAR 並輸出 CSV ===
df = pd.read_csv('players_hitting.csv')
df_2025 = df[df['Season'] == 2025].copy()

if len(df_2025) == 0:
    raise ValueError("資料中沒有 2025 年的紀錄，無法預測 2026 WAR！")

X_2025 = df_2025[features].copy()

# 預測
df_2025['WAR_pred_2026'] = rf_model.predict(X_2025)

output_cols = ['IDfg', 'Name', 'Season', 'WAR', 'WAR_pred_2026']
df_2026_pred = df_2025[output_cols].copy()

# 輸出為 CSV
df_2026_pred.to_csv("predicted(p)_WAR_2026_RF.csv", index=False)

print("\n2026 WAR 預測已輸出至 predicted_WAR_2026_RF.csv !")
