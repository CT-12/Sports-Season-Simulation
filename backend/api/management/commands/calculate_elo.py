"""
Django Management Command: Calculate Elo Ratings

這個命令會讀取 team_game_logs 表中的歷史比賽記錄，
計算每支球隊每天的 Elo 評分，並儲存到 TeamEloHistory model。

Elo 評分系統：
- 初始評分：1500
- K-Factor：20
- MOV 加權：ln(abs(score_diff) + 1)
- 季初回歸：(old_rating * 0.75) + (1500 * 0.25)

使用方式：
    python manage.py calculate_elo --start-year 2021 --end-year 2025
    python manage.py calculate_elo  # 預設計算 2021-2025
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from decimal import Decimal
import math
from datetime import date
from collections import defaultdict


class Command(BaseCommand):
    help = '計算並儲存球隊的 Elo 評分歷史記錄'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-year',
            type=int,
            default=2021,
            help='起始年份 (預設: 2021)'
        )
        parser.add_argument(
            '--end-year',
            type=int,
            default=2025,
            help='結束年份 (預設: 2025)'
        )
        parser.add_argument(
            '--k-factor',
            type=int,
            default=20,
            help='Elo K-Factor (預設: 20)'
        )
        parser.add_argument(
            '--initial-rating',
            type=int,
            default=1500,
            help='初始 Elo 評分 (預設: 1500)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='清除現有的 Elo 記錄'
        )

    def handle(self, *args, **options):
        start_year = options['start_year']
        end_year = options['end_year']
        k_factor = options['k_factor']
        initial_rating = options['initial_rating']
        clear_existing = options['clear_existing']

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'計算 Elo 評分 ({start_year} - {end_year})\n'
            f'{"="*70}\n'
        ))

        # 清除現有記錄 (如果需要)
        if clear_existing:
            self.stdout.write('清除現有 Elo 記錄...')
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM team_elo_history')
            self.stdout.write(self.style.SUCCESS('✓ 已清除'))

        # 讀取所有比賽記錄並按日期排序
        self.stdout.write('\n載入比賽記錄...')
        games = self._load_games(start_year, end_year)
        self.stdout.write(self.style.SUCCESS(f'✓ 載入 {len(games)} 場比賽'))

        # 計算 Elo 評分
        self.stdout.write('\n開始計算 Elo 評分...\n')
        elo_ratings = self._calculate_elo_ratings(
            games, 
            k_factor, 
            initial_rating
        )

        # 儲存到資料庫
        self.stdout.write('\n儲存 Elo 評分到資料庫...')
        saved_count = self._save_elo_ratings(elo_ratings)
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'✓ 完成！儲存 {saved_count} 筆 Elo 評分記錄\n'
            f'{"="*70}\n'
        ))

    def _load_games(self, start_year, end_year):
        """
        從資料庫載入比賽記錄
        
        注意：team_game_logs 是單邊視角，一場比賽有兩筆記錄
        我們需要避免重複計算，只處理 team_id < opponent_id 的記錄
        """
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    game_id,
                    game_date,
                    season,
                    team_id,
                    opponent_id,
                    team_score,
                    opponent_score,
                    result
                FROM team_game_logs
                WHERE season >= %s AND season <= %s
                    AND team_id < opponent_id  -- 避免重複計算
                    AND game_type = 'R'  -- 只計算例行賽
                ORDER BY game_date, game_id
            """
            cursor.execute(sql, [start_year, end_year])
            
            games = []
            for row in cursor.fetchall():
                games.append({
                    'game_id': row[0],
                    'date': row[1],
                    'season': row[2],
                    'team_a_id': row[3],
                    'team_b_id': row[4],
                    'team_a_score': row[5],
                    'team_b_score': row[6],
                    'result': row[7]
                })
            
            return games

    def _calculate_elo_ratings(self, games, k_factor, initial_rating):
        """
        計算所有球隊的 Elo 評分歷史
        
        Returns:
            dict: {(team_id, date): rating_value}
        """
        # 當前 Elo 評分 (每支球隊的最新評分)
        current_ratings = defaultdict(lambda: Decimal(initial_rating))
        
        # 所有歷史記錄 {(team_id, date): rating}
        elo_history = {}
        
        # 追蹤當前賽季
        current_season = None
        
        # 追蹤已處理的球隊 (用於季初回歸)
        teams_in_season = set()
        
        # 處理每一場比賽
        for i, game in enumerate(games, 1):
            game_date = game['date']
            season = game['season']
            team_a_id = game['team_a_id']
            team_b_id = game['team_b_id']
            score_a = game['team_a_score']
            score_b = game['team_b_score']
            
            # 檢測新賽季
            if current_season is None or season != current_season:
                self.stdout.write(f'\n處理 {season} 賽季...')
                
                # 對所有球隊進行季初回歸
                if current_season is not None:
                    self._apply_season_regression(
                        current_ratings, 
                        initial_rating, 
                        elo_history,
                        season,
                        game_date
                    )
                
                current_season = season
                teams_in_season = set()
            
            # 記錄這個賽季出現的球隊
            teams_in_season.add(team_a_id)
            teams_in_season.add(team_b_id)
            
            # 取得當前評分
            rating_a = current_ratings[team_a_id]
            rating_b = current_ratings[team_b_id]
            
            # 計算新的 Elo 評分
            new_rating_a, new_rating_b = self._update_elo_ratings(
                rating_a, rating_b,
                score_a, score_b,
                k_factor
            )
            
            # 更新當前評分
            current_ratings[team_a_id] = new_rating_a
            current_ratings[team_b_id] = new_rating_b
            
            # 記錄歷史
            elo_history[(team_a_id, game_date, season)] = new_rating_a
            elo_history[(team_b_id, game_date, season)] = new_rating_b
            
            # 顯示進度
            if i % 500 == 0:
                self.stdout.write(f'  已處理 {i}/{len(games)} 場比賽...')
        
        return elo_history

    def _apply_season_regression(self, current_ratings, initial_rating, 
                                 elo_history, new_season, reference_date):
        """
        季初回歸：將所有球隊的 Elo 評分拉回平均值
        
        公式：New_Rating = (Old_Rating * 0.75) + (Initial_Rating * 0.25)
        """
        self.stdout.write('  執行季初回歸...')
        
        for team_id in list(current_ratings.keys()):
            old_rating = current_ratings[team_id]
            new_rating = (old_rating * Decimal('0.75')) + (Decimal(initial_rating) * Decimal('0.25'))
            current_ratings[team_id] = new_rating
            
            # 標記為季初評分
            elo_history[(team_id, reference_date, new_season, True)] = new_rating

    def _update_elo_ratings(self, rating_a, rating_b, score_a, score_b, k_factor):
        """
        更新兩支球隊的 Elo 評分
        
        Args:
            rating_a: 球隊 A 當前評分
            rating_b: 球隊 B 當前評分
            score_a: 球隊 A 得分
            score_b: 球隊 B 得分
            k_factor: K-Factor
        
        Returns:
            (new_rating_a, new_rating_b)
        """
        # 計算期望勝率
        expected_a = 1 / (1 + 10 ** ((float(rating_b) - float(rating_a)) / 400))
        expected_b = 1 - expected_a
        
        # 實際結果
        if score_a > score_b:
            actual_a, actual_b = 1, 0
        elif score_a < score_b:
            actual_a, actual_b = 0, 1
        else:
            actual_a, actual_b = 0.5, 0.5
        
        # MOV (Margin of Victory) 加權
        score_diff = abs(score_a - score_b)
        mov_multiplier = math.log(score_diff + 1) if score_diff > 0 else 1
        
        # 計算評分變化
        change_a = Decimal(k_factor) * Decimal(mov_multiplier) * Decimal(actual_a - expected_a)
        change_b = Decimal(k_factor) * Decimal(mov_multiplier) * Decimal(actual_b - expected_b)
        
        # 更新評分
        new_rating_a = rating_a + change_a
        new_rating_b = rating_b + change_b
        
        return new_rating_a, new_rating_b

    def _save_elo_ratings(self, elo_history):
        """
        將 Elo 評分儲存到資料庫
        """
        saved_count = 0
        
        with connection.cursor() as cursor:
            for key, rating in elo_history.items():
                if len(key) == 4:  # 季初回歸記錄
                    team_id, game_date, season, is_season_start = key
                else:  # 一般比賽記錄
                    team_id, game_date, season = key
                    is_season_start = False
                
                sql = """
                    INSERT INTO team_elo_history 
                        (team_id, date, season, rating, is_season_start)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (team_id, date) 
                    DO UPDATE SET 
                        rating = EXCLUDED.rating,
                        is_season_start = EXCLUDED.is_season_start
                """
                cursor.execute(sql, [
                    team_id,
                    game_date,
                    season,
                    rating,
                    is_season_start
                ])
                saved_count += 1
                
                if saved_count % 1000 == 0:
                    self.stdout.write(f'  已儲存 {saved_count} 筆...')
        
        return saved_count
