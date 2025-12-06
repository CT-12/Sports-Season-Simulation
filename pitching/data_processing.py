from pybaseball import fg_pitching_data
import pandas as pd

# 抓資料
def fetch_and_save(start_season=2000, end_season=2025, out_csv='pitching_2000_2025.csv'):
    all_data = []

    for year in range(start_season, end_season + 1):
        print(f"Fetching {year} ...")
        df = fg_pitching_data(year)

        keep_cols = [
            'Season', 'IDfg', 'Name',
            'W', 'L', 'ERA', 'IP', 'H',
            'AVG', 'R', 'ER', 'BB','SO', 'WHIP', 'WAR'
        ]

        cols_present = [c for c in keep_cols if c in df.columns]
        df_small = df[cols_present].copy()

        df_small['Season'] = year
        all_data.append(df_small)

    pitching_all = pd.concat(all_data, ignore_index=True)
    pitching_all.to_csv(out_csv, index=False)
    print(f"Saved {len(pitching_all)} rows to {out_csv}")


# 清理資料：刪除下一年沒有WAR的球員
def clean_data(in_csv='pitching_2000_2025.csv', out_csv='pitching_clean2000.csv'):
    df = pd.read_csv(in_csv)

    df = df.sort_values(['IDfg', 'Season']).reset_index(drop=True)
    df['WAR_next'] = df.groupby('IDfg')['WAR'].shift(-1)

    df_clean = df.dropna(subset=['WAR_next']).copy()
    df_clean.to_csv(out_csv, index=False)

    print(f"Cleaned data saved to {out_csv}")


if __name__ == '__main__':
    fetch_and_save()
    clean_data()
