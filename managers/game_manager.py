# -*- coding: utf-8 -*-
"""游戏管理器 - 核心游戏逻辑"""

import random
from models.player import Player
from managers.board_manager import BoardManager
from ai.ai_player import AIPlayer
from config import *


class GameManager:
    """游戏管理器"""
    
    def __init__(self):
        # 初始化玩家
        self.human_player = Player("玩家", START_CASH, is_ai=False, color=BLUE)
        self.ai_player = Player("AI", START_CASH, is_ai=True, color=RED)
        self.players = [self.human_player, self.ai_player]
        self.current_player_index = 0
        
        # 初始化地图
        self.board = BoardManager(TOTAL_TILES)
        
        # 游戏状态
        self.game_over = False
        self.winner = None
        self.messages = ["点击'投掷骰子'开始游戏"]
        self.waiting_for_buy_decision = False
        self.current_property = None
        
    def add_message(self, new_message):
        """添加新消息并保留最近10条"""
        self.messages.append(new_message)
        if len(self.messages) > 10:
            self.messages.pop(0)
        
    def get_current_player(self):
        """获取当前玩家"""
        return self.players[self.current_player_index]
        
    def roll_dice(self):
        """投掷骰子"""
        if self.game_over or self.waiting_for_buy_decision:
            return None
            
        player = self.get_current_player()
        dice = random.randint(1, 6)
        self.add_message(f"{player.name} 投掷骰子: {dice}")
        
        # 移动玩家
        passed_start = player.move(dice, TOTAL_TILES)
        
        # 经过起点奖励
        if passed_start:
            player.add_cash(START_BONUS)
            self.add_message(f"-> 经过起点 +${START_BONUS}")
            
        return dice
        
    def process_tile_event(self):
        """处理地块事件"""
        player = self.get_current_player()
        tile = self.board.get_tile(player.position)
        
        if tile.tile_type.name == "START":
            self.add_message(f"{player.name} 到达起点")
            return "end_turn"
            
        elif tile.tile_type.name == "PROPERTY":
            return self._handle_property(player, tile)
            
        elif tile.tile_type.name == "CHANCE":
            return self._handle_chance(player)
            
        elif tile.tile_type.name == "TAX":
            return self._handle_tax(player)
            
        return "end_turn"
        
    def _handle_property(self, player, tile):
        """处理地产地块"""
        prop = tile.property
        
        if not prop.has_owner():
            # 无主地产
            if player.is_ai:
                # AI自动决策
                if AIPlayer.decide_buy_property(player, prop):
                    self.buy_property(player, prop)
                    self.add_message(f"{player.name} 购买了 {prop.name} (${prop.price})")
                else:
                    self.add_message(f"{player.name} 放弃购买 {prop.name}")
                return "end_turn"
            else:
                # 玩家需要决策
                self.waiting_for_buy_decision = True
                self.current_property = prop
                if player.can_afford(prop.price):
                    self.add_message(f"是否购买 {prop.name}? 价格: ${prop.price}")
                else:
                    self.add_message(f"{prop.name} 无主，但现金不足 (${prop.price})")
                return "wait"
                
        elif prop.owner != player:
            # 对方地产，支付租金
            return self._pay_rent(player, prop)
            
        else:
            self.add_message(f"{player.name} 到达自己的地产 {prop.name}")
            return "end_turn"
            
    def _pay_rent(self, player, prop):
        """支付租金"""
        rent = prop.rent
        owner = prop.owner
        
        if player.can_afford(rent):
            player.deduct_cash(rent)
            owner.add_cash(rent)
            self.add_message(f"{player.name} 支付 ${rent} 租金给 {owner.name}")
        else:
            # 现金不足，卖地
            self.add_message(f"{player.name} 现金不足！")
            
            if player.properties:
                # 选择一块地产卖给对方
                if player.is_ai:
                    property_to_sell = AIPlayer.choose_property_to_sell(player)
                else:
                    property_to_sell = random.choice(player.properties)
                    
                property_to_sell.transfer_ownership(owner, player)
                self.add_message(f"-> 将 {property_to_sell.name} 转让给 {owner.name}")
                
                # 支付剩余租金
                owner.add_cash(player.cash)
                player.cash = 0
            else:
                # 无地产可卖，现金也不足
                self.add_message("-> 无资产可变卖！")
                
        return "end_turn"
        
    def _handle_chance(self, player):
        """处理机会事件"""
        event_type = random.randint(0, 2)
        
        if event_type == 0:
            # 获得奖金
            bonus = random.randint(100, 500)
            player.add_cash(bonus)
            self.add_message(f"{player.name} 获得奖金 ${bonus}")
        elif event_type == 1:
            # 支付罚款
            penalty = random.randint(100, 300)
            player.deduct_cash(penalty)
            self.add_message(f"{player.name} 支付罚款 ${penalty}")
        else:
            # 位置移动
            move_steps = random.randint(-3, 3)
            if move_steps != 0:
                player.move(move_steps, TOTAL_TILES)
                self.add_message(f"{player.name} 移动 {move_steps} 格")
                
        return "end_turn"
        
    def _handle_tax(self, player):
        """处理税收"""
        tax = 200
        player.deduct_cash(tax)
        self.add_message(f"{player.name} 缴纳税金 ${tax}")
        return "end_turn"
        
    def buy_property(self, player, prop):
        """购买地产"""
        if player.can_afford(prop.price):
            player.deduct_cash(prop.price)
            prop.transfer_ownership(player)
            return True
        return False
        
    def player_buy_decision(self, buy):
        """玩家购买决策"""
        if not self.waiting_for_buy_decision:
            return
            
        player = self.human_player
        prop = self.current_property
        
        if buy and self.buy_property(player, prop):
            self.add_message(f"购买成功！获得 {prop.name}")
        else:
            self.add_message(f"放弃购买 {prop.name}")
            
        self.waiting_for_buy_decision = False
        self.current_property = None
        
    def check_game_over(self):
        """检查游戏是否结束"""
        if self.human_player.get_total_wealth() <= 0:
            self.game_over = True
            self.winner = self.ai_player
            self.add_message("游戏结束！AI 获胜！")
            return True
            
        if self.ai_player.get_total_wealth() <= 0:
            self.game_over = True
            self.winner = self.human_player
            self.add_message("游戏结束！玩家 获胜！")
            return True
            
        return False
        
    def next_turn(self):
        """下一回合"""
        if self.check_game_over():
            return
            
        self.current_player_index = (self.current_player_index + 1) % 2
        player = self.get_current_player()
        self.add_message(f"轮到 {player.name} 行动")

