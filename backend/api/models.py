from django.db import models


class TeamEloHistory(models.Model):
    """
    儲存球隊每日的 Elo 評分歷史記錄
    
    Elo 評分系統用於動態追蹤球隊實力變化，每場比賽後更新。
    季初會進行回歸平均 (soft reset) 以反映新賽季的不確定性。
    """
    team_id = models.IntegerField(db_index=True, help_text="球隊 ID")
    date = models.DateField(db_index=True, help_text="評分日期")
    season = models.IntegerField(db_index=True, help_text="賽季年份")
    rating = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Elo 評分 (通常在 1200-1800 之間)"
    )
    is_season_start = models.BooleanField(
        default=False,
        help_text="是否為季初回歸後的初始分數"
    )
    
    class Meta:
        db_table = 'team_elo_history'
        unique_together = ['team_id', 'date']
        ordering = ['date', 'team_id']
        indexes = [
            models.Index(fields=['team_id', 'season']),
            models.Index(fields=['season', 'date']),
        ]
        verbose_name = 'Team Elo History'
        verbose_name_plural = 'Team Elo Histories'
    
    def __str__(self):
        return f"Team {self.team_id} - {self.date}: {self.rating}"


# Note: This app primarily acts as a proxy to MLB Stats API,
# so we don't define complex models here. Data models are handled
# by the external API.
# Models can be added later if we need to cache data or store custom information.
