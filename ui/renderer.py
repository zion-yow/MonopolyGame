# -*- coding: utf-8 -*-
"""游戏渲染器"""

import pygame
from config import *


class Renderer:
    """渲染器"""
    
    def __init__(self, screen):
        self.screen = screen
        # 使用系统字体支持中文显示
        # 优先使用微软雅黑，如果没有则尝试其他中文字体
        try:
            self.font = pygame.font.SysFont('microsoftyahei,simsun,simhei,arial', 24)
            self.large_font = pygame.font.SysFont('microsoftyahei,simsun,simhei,arial', 36)
            self.small_font = pygame.font.SysFont('microsoftyahei,simsun,simhei,arial', 20)
        except:
            # 如果系统字体加载失败，使用默认字体
            self.font = pygame.font.Font(None, 24)
            self.large_font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 20)
        
    def draw_tile(self, tile):
        """绘制地块"""
        x, y = tile.position
        color = tile.get_color()
        
        # 绘制方形地块
        rect = pygame.Rect(x - TILE_SIZE//2, y - TILE_SIZE//2, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, BLACK, rect, 2)
        
        # 绘制地块编号
        text = self.small_font.render(str(tile.index), True, BLACK)
        text_rect = text.get_rect(center=(x, y))
        self.screen.blit(text, text_rect)
        
    def draw_player(self, position, color, is_ai=False):
        """绘制玩家"""
        x, y = position
        pygame.draw.circle(self.screen, color, (int(x), int(y)), 12)
        pygame.draw.circle(self.screen, BLACK, (int(x), int(y)), 12, 2)
        
    def draw_text(self, text, position, color=BLACK, font=None):
        """绘制文本"""
        if font is None:
            font = self.font
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)
        
    def draw_messages(self, messages, x, y):
        """绘制消息列表"""
        for i, message in enumerate(messages):
            # 最近的消息颜色更深
            color_value = max(0, 200 - i * 20)
            color = (color_value, color_value, color_value)
            self.draw_text(message, (x, y + i * 22), color, self.small_font)
        
    def draw_button(self, rect, text, active=True):
        """绘制按钮"""
        color = BLUE if active else GRAY
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, BLACK, rect, 2)
        
        text_surface = self.font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
        
    def draw_sell_buttons(self, properties, x, y):
        """绘制出售地产的按钮"""
        buttons = []
        for i, prop in enumerate(properties):
            rect = pygame.Rect(x, y + i * 45, BUTTON_WIDTH + 50, BUTTON_HEIGHT)
            self.draw_button(rect, f"出售 {prop.name} (${prop.price})")
            buttons.append((rect, prop.tile_index))
        return buttons

    def draw_info_panel(self, player, x, y):
        """绘制信息面板"""
        texts = [
            f"{player.name}",
            f"现金: ${player.cash}",
            f"资产数: {len(player.properties)}",
            f"总财富: ${player.get_total_wealth()}",
            f"利率: {player.interest_rate * 100:.2f}%",
            f"土地税率: {player.tax_rate * 100:.2f}%"
        ]
        
        for i, text in enumerate(texts):
            self.draw_text(text, (x, y + i * 30))

