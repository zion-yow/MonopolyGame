# -*- coding: utf-8 -*-
"""大富翁游戏 - 主程序入口"""

import pygame
import sys
from managers.game_manager import GameManager
from ui.renderer import Renderer
from config import *


class MonopolyGame:
    """大富翁游戏主类"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("大富翁游戏")
        self.clock = pygame.time.Clock()
        
        # 初始化管理器
        self.game_manager = GameManager()
        self.renderer =Renderer(self.screen)
        
        # UI元素
        self.roll_button = pygame.Rect(INFO_PANEL_X, 450, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buy_button = pygame.Rect(INFO_PANEL_X, 510, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.skip_button = pygame.Rect(INFO_PANEL_X, 570, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.end_turn_button = pygame.Rect(INFO_PANEL_X, 630, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.sell_buttons = []
        
        self.action_taken = False
        self.ai_auto_play_delay = 0
        
    def run(self):
        """游戏主循环"""
        running = True
        
        while running:
            # 控制帧率
            self.clock.tick(FPS)
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.pos)
                    
            # AI自动行动
            if not self.game_manager.game_over:
                current_player = self.game_manager.get_current_player()
                if (current_player.is_ai 
                        and not self.game_manager.waiting_for_buy_decision
                        and not self.game_manager.waiting_for_sell_decision):
                    self.ai_auto_play_delay += 1
                    if self.ai_auto_play_delay > 30:  # 1秒延迟
                        if not self.action_taken:
                            self.game_manager.roll_dice()
                            result = self.game_manager.process_tile_event()
                            if result == "end_turn":
                                self.action_taken = False
                                self.game_manager.next_turn()
                            else:
                                self.action_taken = True
                        else:
                            self.action_taken = False
                            self.game_manager.next_turn()
                        self.ai_auto_play_delay = 0
                        
            # 渲染
            self.render()
            
        pygame.quit()
        sys.exit()
        
    def handle_mouse_click(self, pos):
        """处理鼠标点击"""
        if self.game_manager.game_over:
            return
            
        current_player = self.game_manager.get_current_player()
        
        # 只有玩家回合才能点击
        if current_player.is_ai:
            return
            
        # 出售地产按钮
        if self.game_manager.waiting_for_sell_decision:
            for rect, tile_index in self.sell_buttons:
                if rect.collidepoint(pos):
                    result = self.game_manager.sell_property(current_player, tile_index)
                    if result == "paid":
                        followup = self.game_manager.handle_post_payment()
                        if followup == "end_turn":
                            self.action_taken = True
                        elif followup == "wait":
                            # 等待新的事件处理，例如购买决策
                            pass
                        else:
                            if followup == "end_turn":
                                self.action_taken = True
                    elif result == "bankrupt":
                        self.action_taken = True
                    return
        
        # 投掷骰子按钮
        if self.roll_button.collidepoint(pos) and not self.action_taken:
            self.game_manager.roll_dice()
            result = self.game_manager.process_tile_event()
            if result == "end_turn":
                self.action_taken = True
            elif result == "wait":
                # 等待玩家决策
                pass
                
        # 购买按钮
        elif self.buy_button.collidepoint(pos) and self.game_manager.waiting_for_buy_decision:
            self.game_manager.player_buy_decision(True)
            self.action_taken = True
            
        # 跳过按钮
        elif self.skip_button.collidepoint(pos) and self.game_manager.waiting_for_buy_decision:
            self.game_manager.player_buy_decision(False)
            self.action_taken = True
            
        # 结束回合按钮
        elif self.end_turn_button.collidepoint(pos) and self.action_taken:
            self.game_manager.next_turn()
            self.action_taken = False
            
    def render(self):
        """渲染游戏画面"""
        self.screen.fill(WHITE)
        
        # 绘制地图
        for tile in self.game_manager.board.tiles:
            self.renderer.draw_tile(tile)
            
        # 绘制玩家
        for player in self.game_manager.players:
            pos = self.game_manager.board.get_player_position(
                player.position, player.is_ai
            )
            self.renderer.draw_player(pos, player.color, player.is_ai)
            
        # 绘制信息面板
        self.renderer.draw_info_panel(self.game_manager.human_player, INFO_PANEL_X, 50)
        self.renderer.draw_info_panel(self.game_manager.ai_player, INFO_PANEL_X, 250)
        
        # 绘制消息
        self.renderer.draw_messages(self.game_manager.messages, 700, 50)
        
        # 绘制按钮
        current_player = self.game_manager.get_current_player()
        is_player_turn = not current_player.is_ai
        
        self.renderer.draw_button(
            self.roll_button, 
            "投掷骰子", 
            is_player_turn and not self.action_taken and not self.game_manager.game_over
        )
        
        if self.game_manager.waiting_for_buy_decision:
            self.renderer.draw_button(self.buy_button, "购买", True)
            self.renderer.draw_button(self.skip_button, "跳过", True)
        else:
            self.renderer.draw_button(self.buy_button, "购买", False)
            self.renderer.draw_button(self.skip_button, "跳过", False)
            
        self.renderer.draw_button(
            self.end_turn_button, 
            "结束回合", 
            is_player_turn and self.action_taken
        )
        
        # 绘制出售按钮
        if self.game_manager.waiting_for_sell_decision:
            self.sell_buttons = self.renderer.draw_sell_buttons(
                self.game_manager.properties_to_sell, 
                INFO_PANEL_X, 
                510
            )
        else:
            self.sell_buttons = []

        # 游戏结束提示
        if self.game_manager.game_over:
            text = f"游戏结束！{self.game_manager.winner.name} 获胜！"
            self.renderer.draw_text(text, (300, 350), RED, self.renderer.large_font)
            
        pygame.display.flip()


if __name__ == "__main__":
    game = MonopolyGame()
    game.run()

