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
        
        # 如果有地产，绘制等级信息
        if tile.property and tile.property.owner:
            level_text = self.small_font.render(f"Lv{tile.property.level}", True, (100, 100, 100))
            level_rect = level_text.get_rect(center=(x, y + 8))
            self.screen.blit(level_text, level_rect)
        
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
        
    def draw_messages(self, messages, x, y, is_player_turn=True):
        """绘制消息列表"""
        for i, message in enumerate(messages):
            # 最近的消息颜色更深
            if is_player_turn:
                # 玩家回合：蓝色系
                base_color_value = 100  # 蓝色
                color_value = base_color_value + (len(messages) - 1 - i) * 10
                color = (max(0, color_value - 50), max(0, color_value - 50), min(255, color_value + 55))
            else:
                # AI回合：红色系
                base_color_value = 100  # 红色
                color_value = base_color_value + (len(messages) - 1 - i) * 10
                color = (min(255, color_value + 55), max(0, color_value - 50), max(0, color_value - 50))
            
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
            self.draw_button(rect, f"出售 {prop.name} (${prop.property_price})")
            buttons.append((rect, prop.tile_index))
        return buttons

    def draw_info_panel(self, player, x, y, cpi=0):
        """绘制信息面板"""
        texts = [
            f"{player.name}",
            f"现金: ${player.cash}",
            f"资产数: {len(player.properties)}",
            f"总财富: ${player.get_total_wealth()}",
            f"利率: {player.interest_rate * 100:.2f}%",
            f"土地税率: {player.tax_rate * 100:.2f}%",
            f"物价指数: {cpi * 100:.2f}%"
        ]
        
        for i, text in enumerate(texts):
            self.draw_text(text, (x, y + i * 25))
    
    def draw_property_tooltip(self, prop, cpi, x, y):
        """绘制地产信息提示"""
        if prop:
            prop.update_property_price(cpi)
            texts = [
                f"{prop.name}",
                f"等级: {prop.level}/{5}",
                f"地产价格: ${prop.property_price}",
                f"租金: ${int(prop.property_price * prop.rent_rate)}",
                f"升级成本: ${prop.get_upgrade_cost(cpi) if prop.can_upgrade() else 0}",
                f"维护成本: ${prop.get_maintenance_cost(cpi)}"
            ]
            for i, text in enumerate(texts):
                self.draw_text(text, (x, y + i * 20), (100, 100, 100), self.small_font)

