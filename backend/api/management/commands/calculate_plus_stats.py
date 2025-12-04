"""
Django Management Command: Calculate ERA+ and OPS+

Calculates ERA+ and OPS+ for all players from 2021-2025 and stores them
in the database.

ERA+ Formula: 100 × (lgERA / playerERA)
OPS+ Formula: 100 × (playerOPS / lgOPS)

100 = League average
>100 = Above average
<100 = Below average

Usage:
    python manage.py calculate_plus_stats
    python manage.py calculate_plus_stats --start-year 2021 --end-year 2025
"""

from django.core.management.base import BaseCommand
from django.db import connection
from decimal import Decimal


class Command(BaseCommand):
    help = 'Calculate and store ERA+ and OPS+ statistics for all players'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-year',
            type=int,
            default=2021,
            help='Start year (default: 2021)'
        )
        parser.add_argument(
            '--end-year',
            type=int,
            default=2025,
            help='End year (default: 2025)'
        )

    def handle(self, *args, **options):
        start_year = options['start_year']
        end_year = options['end_year']

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'計算 ERA+ 和 OPS+ ({start_year} - {end_year})\n'
            f'{"="*70}\n'
        ))

        # Add columns if they don't exist
        self._ensure_columns_exist()

        # Calculate for each season
        total_updated = 0
        for season in range(start_year, end_year + 1):
            self.stdout.write(f'\n處理 {season} 賽季...')
            
            ops_count = self._calculate_ops_plus(season)
            era_count = self._calculate_era_plus(season)
            
            total_updated += ops_count + era_count
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ OPS+: {ops_count} 位球員\n'
                f'  ✓ ERA+: {era_count} 位投手'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'✓ 完成！更新 {total_updated} 筆記錄\n'
            f'{"="*70}\n'
        ))

    def _ensure_columns_exist(self):
        """確保資料表有 ops_plus 和 era_plus 欄位"""
        self.stdout.write('檢查資料表欄位...')
        
        with connection.cursor() as cursor:
            # Check and add ops_plus column
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='player_hitting_stats' 
                    AND column_name='ops_plus'
            """)
            if not cursor.fetchone():
                self.stdout.write('  新增 ops_plus 欄位到 player_hitting_stats...')
                cursor.execute("""
                    ALTER TABLE player_hitting_stats 
                    ADD COLUMN ops_plus INTEGER
                """)
            
            # Check and add era_plus column
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='player_pitching_stats' 
                    AND column_name='era_plus'
            """)
            if not cursor.fetchone():
                self.stdout.write('  新增 era_plus 欄位到 player_pitching_stats...')
                cursor.execute("""
                    ALTER TABLE player_pitching_stats 
                    ADD COLUMN era_plus INTEGER
                """)
        
        self.stdout.write(self.style.SUCCESS('  ✓ 欄位檢查完成'))

    def _calculate_ops_plus(self, season: int) -> int:
        """
        Calculate OPS+ for all hitters in a season.
        
        Formula: OPS+ = 100 × (playerOPS / lgOPS)
        
        Args:
            season: Year to calculate
        
        Returns:
            int: Number of players updated
        """
        with connection.cursor() as cursor:
            # Get league average OPS (qualified hitters only)
            cursor.execute("""
                SELECT AVG(ops) as lg_ops
                FROM player_hitting_stats
                WHERE season = %s 
                    AND ab >= 100  -- Qualified hitters
                    AND ops IS NOT NULL
            """, [season])
            
            row = cursor.fetchone()
            if not row or row[0] is None:
                self.stdout.write(self.style.WARNING(
                    f'  警告: {season} 賽季無 OPS 數據'
                ))
                return 0
            
            lg_ops = float(row[0])
            
            # Calculate OPS+ for all players
            cursor.execute("""
                UPDATE player_hitting_stats
                SET ops_plus = CASE 
                    WHEN ops IS NOT NULL AND ops > 0 
                    THEN LEAST(999, GREATEST(0, ROUND(100.0 * ops / %s)))
                    ELSE NULL 
                END
                WHERE season = %s
                    AND ops IS NOT NULL
            """, [lg_ops, season])
            
            return cursor.rowcount

    def _calculate_era_plus(self, season: int) -> int:
        """
        Calculate ERA+ for all pitchers in a season.
        
        Formula: ERA+ = 100 × (lgERA / playerERA)
        
        Args:
            season: Year to calculate
        
        Returns:
            int: Number of pitchers updated
        """
        with connection.cursor() as cursor:
            # Get league average ERA (qualified pitchers only)
            cursor.execute("""
                SELECT AVG(era) as lg_era
                FROM player_pitching_stats
                WHERE season = %s 
                    AND ip >= 50  -- Qualified pitchers
                    AND era IS NOT NULL
                    AND era > 0
            """, [season])
            
            row = cursor.fetchone()
            if not row or row[0] is None:
                self.stdout.write(self.style.WARNING(
                    f'  警告: {season} 賽季無 ERA 數據'
                ))
                return 0
            
            lg_era = float(row[0])
            
            # Calculate ERA+ for all pitchers
            cursor.execute("""
                UPDATE player_pitching_stats
                SET era_plus = CASE 
                    WHEN era IS NOT NULL AND era > 0 
                    THEN LEAST(999, GREATEST(0, ROUND(100.0 * %s / era)))
                    ELSE NULL 
                END
                WHERE season = %s
                    AND era IS NOT NULL
                    AND era > 0
            """, [lg_era, season])
            
            return cursor.rowcount
