import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow.keras.layers import Dense, Input, Dropout, BatchNormalization
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import tensorflow as tf

from tensorflow.keras.models import Sequential
import matplotlib.pyplot as plt

# 讀取資料
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

# 標準化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled   = scaler.transform(X_val)
X_test_scaled  = scaler.transform(X_test)

num_features = X_train_scaled.shape[1]

# 模型
model = Sequential([
    Input(shape=(num_features,)),
    Dense(128, activation='relu'),
    Dropout(0.1),
    Dense(128, activation='relu'),
    Dense(64, activation='relu'),
    Dense(1)
])

opt = tf.keras.optimizers.Adam(learning_rate=1e-3)

model.compile(
    optimizer=opt,
    loss='mse',
    metrics=['mae']
)

# callbacks
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=20,
    restore_best_weights=True
)

reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=6,
    min_lr=1e-6,
    verbose=1
)

# 訓練
history = model.fit(
    X_train_scaled, y_train,
    validation_data=(X_val_scaled, y_val),
    epochs=300,
    batch_size=32,
    callbacks=[early_stop, reduce_lr],
    verbose=2
)

# 驗證集預測
y_val_pred = model.predict(X_val_scaled).flatten()
mae_val = mean_absolute_error(y_val, y_val_pred)
rmse_val = np.sqrt(mean_squared_error(y_val, y_val_pred))
r2_val = r2_score(y_val, y_val_pred)

print("=== 驗證集評估指標 ===")
print("MAE :", mae_val)
print("RMSE:", rmse_val)
print("R²  :", r2_val)

# 測試集預測
y_test_pred = model.predict(X_test_scaled).flatten()
mae_test = mean_absolute_error(y_test, y_test_pred)
rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
r2_test = r2_score(y_test, y_test_pred)

print("=== 測試集評估指標 ===")
print("MAE :", mae_test)
print("RMSE:", rmse_test)
print("R²  :", r2_test)

# Loss 曲線
plt.figure(figsize=(8,5))
plt.plot(history.history['loss'], label='train_loss')
plt.plot(history.history['val_loss'], label='val_loss')
plt.xlabel('Epoch')
plt.ylabel('MSE Loss')
plt.title('Training & Validation Loss')
plt.legend()
plt.show()

# === 用 2025 的數據預測 2026 WAR 並輸出 CSV (Keras 版本修正) ===

# 讀取資料
df = pd.read_csv('players_hitting.csv')
df_2025 = df[df['Season'] == 2025].copy()

if len(df_2025) == 0:
    raise ValueError("資料中沒有 2025 年的紀錄，無法預測 2026 WAR！")

X_2025 = df_2025[features].copy()


X_2025_scaled = scaler.transform(X_2025)

y_2026_pred = model.predict(X_2025_scaled).flatten()

df_2025['WAR_pred_2026'] = y_2026_pred

output_cols = ['IDfg', 'Name', 'Season', 'WAR', 'WAR_pred_2026']
df_2026_pred = df_2025[output_cols].copy()

# 儲存 CSV
df_2026_pred.to_csv("predicted_WAR_2026_Keras.csv", index=False)

print("\n2026 WAR 預測已輸出至 predicted_WAR_2026_Keras.csv !")
