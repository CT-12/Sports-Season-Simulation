import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb 
from xgboost.callback import EarlyStopping

df = pd.read_csv('batting_clean2000.csv')

features = ['AB', 'R', 'H', 'HR', 'RBI',
            'AVG', 'OBP', 'SLG', 'OPS', 'WAR']

target = 'WAR_next'

X = df[features].copy()
y = df[target].copy()

# 時間切分
train_idx = df['Season'] < 2023
val_idx   = df['Season'] == 2023
test_idx  = df['Season'] == 2024

X_train, X_val, X_test = X[train_idx], X[val_idx], X[test_idx]
y_train, y_val, y_test = y[train_idx], y[val_idx], y[test_idx]

# 轉 DMatrix
dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=features)
dval   = xgb.DMatrix(X_val,   label=y_val,   feature_names=features)
dtest  = xgb.DMatrix(X_test,  feature_names=features)

print("Data loaded without standardization!")

params = {
    'objective': 'reg:squarederror',
    'eval_metric': 'rmse',
    'max_depth': 3,
    'learning_rate': 0.01,
    'min_child_weight': 2,
    'gamma': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'seed': 42,
    'nthread': -1
}

early_stopping = EarlyStopping(
    rounds=20,
    metric_name='rmse',
    data_name='validation_0'
)

xgb_model_raw = xgb.train(
    params,
    dtrain,
    num_boost_round=1000,
    evals=[(dval, 'validation_0')],
    callbacks=[early_stopping],
    verbose_eval=20
)

# 驗證集
y_val_pred = xgb_model_raw.predict(dval)
mae_val = mean_absolute_error(y_val, y_val_pred)
rmse_val = np.sqrt(mean_squared_error(y_val, y_val_pred))
r2_val = r2_score(y_val, y_val_pred)

print("=== 驗證集評估指標 ===")
print("MAE :", mae_val)
print("RMSE:", rmse_val)
print("R²  :", r2_val)

# 測試集
y_test_pred = xgb_model_raw.predict(dtest)
mae_test = mean_absolute_error(y_test, y_test_pred)
rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
r2_test = r2_score(y_test, y_test_pred)

print("=== 測試集評估指標 ===")
print("MAE :", mae_test)
print("RMSE:", rmse_test)
print("R²  :", r2_test)


# 輸出特徵權重比例
importance = xgb_model_raw.get_score(importance_type='weight')
importance_df = pd.DataFrame({
    'Feature': list(importance.keys()),
    'Weight': list(importance.values())
})
importance_df['Ratio'] = importance_df['Weight'] / importance_df['Weight'].sum() * 100
importance_df = importance_df.sort_values(by='Ratio', ascending=False).reset_index(drop=True)

print("\n=== 特徵權重比例 ===")
print(importance_df)

# === 用 2025 的數據預測 2026 WAR 並輸出 CSV ===

df = pd.read_csv('players_hitting.csv')
df_2025 = df[df['Season'] == 2025].copy()

if len(df_2025) == 0:
    raise ValueError("資料中沒有 2025 年的紀錄，無法預測 2026 WAR！")

X_2025 = df_2025[features].copy()
d2025 = xgb.DMatrix(X_2025, feature_names=features)

# 預測
df_2025['WAR_pred_2026'] = xgb_model_raw.predict(d2025)

output_cols = ['IDfg', 'Name', 'Season', 'WAR', 'WAR_pred_2026']
df_2026_pred = df_2025[output_cols].copy()

# 儲存 CSV
df_2026_pred.to_csv("predicted_WAR_2026_XGB.csv", index=False)

print("\n2026 WAR 預測已輸出至 predicted_WAR_2026_XGB.csv !")

