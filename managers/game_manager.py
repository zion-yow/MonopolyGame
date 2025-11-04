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
        
        # CPI 管理
        self.cpi = INITIAL_CPI
        self.last_total_wealth = START_CASH*2
        
        # 游戏状态
        self.game_over = False
        self.winner = None
        self.messages = ["点击'投掷骰子'开始游戏"]
        self.waiting_for_buy_decision = False
        self.waiting_for_sell_decision = False
        self.waiting_for_upgrade_decision = False
        self.upgrade_property = None
        self.properties_to_sell = []
        self.pending_payment_amount = 0
        self.pending_payment_receiver = None
        self.pending_payment_type = None
        self.pending_followup_action = None
        self.post_payment_action = None
        self.cached_process_result = None
        self.current_property = None
        
    def add_message(self, new_message):
        """添加新消息并保留最近10条"""
        self.messages.append(new_message)
        if len(self.messages) > 10:
            self.messages.pop(0)
        
    def get_current_player(self):
        """获取当前玩家"""
        return self.players[self.current_player_index]
        
    def _clamp(self, value, min_value, max_value):
        return max(min_value, min(value, max_value))
        
    def _format_percentage(self, value):
        return f"{value * 100:.2f}%"
        
    def get_total_game_wealth(self):
        """计算游戏总财富"""
        total = sum(player.cash for player in self.players)
        total += sum(
            prop.property_price 
            for tile in self.board.tiles 
            for prop in ([tile.property] if tile.property else [])
        )
        return total
    
    def update_cpi(self):
        """根据总财富变化更新CPI"""
        current_wealth = self.get_total_game_wealth()
        wealth_delta = current_wealth - self.last_total_wealth
        self.last_total_wealth = current_wealth
        
        # 每百万财富变化影响CPI
        wealth_change_impact = (wealth_delta / 1000000) * CPI_CHANGE_PER_TOTAL_WEALTH
        new_cpi = self._clamp(
            self.cpi + wealth_change_impact,
            CPI_MIN,
            CPI_MAX
        )
        
        if abs(new_cpi - self.cpi) > 0.001:  # 只在变化显著时更新
            old_cpi = self.cpi
            self.cpi = new_cpi
            self.add_message(f"物价指数更新: {self._format_percentage(old_cpi)} → {self._format_percentage(self.cpi)}")
            return True
        return False
    
    def apply_cpi_fluctuation(self, delta):
        """外部触发CPI浮动（如CHANCE事件）"""
        new_cpi = self._clamp(
            self.cpi + delta,
            CPI_MIN,
            CPI_MAX
        )
        if abs(new_cpi - self.cpi) > 0.001:
            self.cpi = new_cpi
            self.add_message(f"-> 物价指数浮动: {self._format_percentage(self.cpi)}")

    def apply_start_effects(self, player):
        """结算经过起点时的利息与土地税"""
        self.add_message(f"{player.name} 经过起点，结算利息与土地税")
        wait_required = False
        
        # 发放现金利息
        interest_gain = int(player.cash * player.interest_rate)
        if interest_gain > 0:
            player.add_cash(interest_gain)
            self.add_message(
                f"-> 获得利息 ${interest_gain} (利率 {self._format_percentage(player.interest_rate)})"
            )
        else:
            self.add_message(
                f"-> 当前利率 {self._format_percentage(player.interest_rate)}，未获得利息"
            )
        
        # 征收土地税
        total_property_value = sum(prop.property_price for prop in player.properties)
        tax_due = int(total_property_value * player.tax_rate)
        if tax_due > 0:
            if player.can_afford(tax_due):
                player.deduct_cash(tax_due)
                self.add_message(
                    f"-> 支付土地税 ${tax_due} (税率 {self._format_percentage(player.tax_rate)})"
                )
            else:
                self.add_message(
                    f"-> 应缴土地税 ${tax_due} (税率 {self._format_percentage(player.tax_rate)})，现金不足！"
                )
                result = self.enter_sell_mode(player, tax_due, None, payment_type="tax", followup="continue_tile")
                if result == "wait":
                    wait_required = True
        else:
            self.add_message(
                f"-> 当前土地税率 {self._format_percentage(player.tax_rate)}，无需缴税"
            )
        
        # 调整下一次的利率与税率
        self.adjust_rates(player)
        
        return wait_required
        
    def adjust_rates(self, player):
        """每次经过起点后令利率和税率浮动"""
        interest_delta = random.uniform(-INTEREST_RATE_FLUCTUATION, INTEREST_RATE_FLUCTUATION)
        tax_delta = random.uniform(-TAX_RATE_FLUCTUATION, TAX_RATE_FLUCTUATION)
        
        player.interest_rate = self._clamp(
            player.interest_rate + interest_delta,
            INTEREST_RATE_MIN,
            INTEREST_RATE_MAX
        )
        player.tax_rate = self._clamp(
            player.tax_rate + tax_delta,
            TAX_RATE_MIN,
            TAX_RATE_MAX
        )
        
        self.add_message(
            f"-> 新利率 {self._format_percentage(player.interest_rate)}，新土地税率 {self._format_percentage(player.tax_rate)}"
        )
        
    def roll_dice(self):
        """投掷骰子"""
        if self.game_over or self.waiting_for_buy_decision:
            return None
            
        player = self.get_current_player()
        dice = random.randint(1, 6)
        self.add_message(f"{player.name} 投掷骰子: {dice}")
        
        # 移动玩家
        passed_start = player.move(dice, TOTAL_TILES)
        
        # 经过起点结算
        if passed_start:
            wait_required = self.apply_start_effects(player)
            if wait_required:
                return dice
        
        return dice
        
    def process_tile_event(self):
        """处理地块事件"""
        if self.cached_process_result is not None:
            result = self.cached_process_result
            self.cached_process_result = None
            return result
        
        if self.waiting_for_sell_decision:
            return "wait"
        
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
                    self.add_message(f"{player.name} 购买了 {prop.name} (${prop.base_price})")
                else:
                    self.add_message(f"{player.name} 放弃购买 {prop.name}")
                return "end_turn"
            else:
                # 玩家需要决策
                self.waiting_for_buy_decision = True
                self.current_property = prop
                if player.can_afford(prop.base_price):
                    self.add_message(f"是否购买 {prop.name}? 价格: ${prop.base_price}")
                else:
                    self.add_message(f"{prop.name} 无主，但现金不足 (${prop.base_price})")
                return "wait"
                
        elif prop.owner != player:
            # 对方地产，支付租金
            rent = prop.get_rent(self.cpi)
            owner = prop.owner
            if not player.can_afford(rent):
                result = self.enter_sell_mode(player, rent, owner, payment_type="rent", followup="end_turn")
                return result if result else "wait"
            else:
                player.deduct_cash(rent)
                owner.add_cash(rent)
                self.add_message(f"{player.name} 支付 ${rent} 租金给 {owner.name}（地产等级{prop.level}）")
                return "end_turn"
            
        else:
            self.add_message(f"{player.name} 到达自己的地产 {prop.name}（等级{prop.level}）")
            
            # 提示升级选项
            if prop.can_upgrade():
                upgrade_cost = prop.get_upgrade_cost(self.cpi)
                if player.can_afford(upgrade_cost):
                    self.add_message(
                        f"-> 可升级！升级成本 ${upgrade_cost}（新等级{prop.level + 1}/{PROPERTY_MAX_LEVEL}）"
                    )
                    
                    if player.is_ai:
                        # AI自动升级
                        if random.random() > 0.3:  # AI 70%概率升级
                            prop.upgrade()
                            player.deduct_cash(upgrade_cost)
                            self.add_message(f"-> {player.name} 升级了 {prop.name}！")
                    else:
                        # 玩家手动选择
                        self.waiting_for_upgrade_decision = True
                        self.upgrade_property = prop
                        self.add_message(f"-> 是否升级？点击升级或跳过按钮")
                        return "wait"
                else:
                    self.add_message(f"-> 想升级但现金不足（需要 ${upgrade_cost}）")
            
            # 支付维护成本
            maintenance = prop.get_maintenance_cost(self.cpi)
            if maintenance > 0:
                if player.can_afford(maintenance):
                    player.deduct_cash(maintenance)
                    self.add_message(f"-> 支付维护成本 ${maintenance}")
                else:
                    self.add_message(f"-> 无法支付维护成本 ${maintenance}！")
            
            return "end_turn"
            
    def _handle_chance(self, player):
        """处理机会事件"""
        event_type = random.randint(0, 3)  # 增加到4种事件类型以包含CPI事件
        
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
        elif event_type == 2:
            # 位置移动
            move_steps = random.choice([i for i in range(-6, 7) if i != 0])
            if move_steps != 0:
                player.move(move_steps, TOTAL_TILES)
                self.add_message(f"{player.name} 移动 {move_steps} 格")
                self.process_tile_event()
        else:
            # 物价指数浮动
            delta = random.uniform(CHANCE_CPI_FLUCTUATION[0], CHANCE_CPI_FLUCTUATION[1])
            direction = "上升" if delta > 0 else "下降"
            self.add_message(f"{player.name} 触发突发事件：物价指数{direction}！")
            self.apply_cpi_fluctuation(delta)
                
        return "end_turn"
        
    def _handle_tax(self, player):
        """处理税收"""
        tax = 200
        player.deduct_cash(tax)
        self.add_message(f"{player.name} 缴纳税金 ${tax}")
        return "end_turn"
        
    def buy_property(self, player, prop):
        """购买地产"""
        if player.can_afford(prop.base_price):
            player.deduct_cash(prop.base_price)
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
    
    def player_upgrade_decision(self, upgrade):
        """玩家升级决策"""
        if not self.waiting_for_upgrade_decision:
            return
        
        player = self.human_player
        prop = self.upgrade_property
        
        if upgrade:
            upgrade_cost = prop.get_upgrade_cost(self.cpi)
            if player.can_afford(upgrade_cost):
                prop.upgrade()
                player.deduct_cash(upgrade_cost)
                self.add_message(f"升级成功！{prop.name} 现在是 Lv{prop.level}")
            else:
                self.add_message(f"现金不足！")
        else:
            self.add_message(f"放弃升级 {prop.name}")
        
        self.waiting_for_upgrade_decision = False
        self.upgrade_property = None

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
        
        # 更新CPI
        self.update_cpi()

    def enter_sell_mode(self, player, amount, owner, payment_type="rent", followup="end_turn"):
        """进入出售地产模式"""
        self.pending_payment_amount = amount
        self.pending_payment_receiver = owner
        self.pending_payment_type = payment_type
        self.pending_followup_action = followup
        self.post_payment_action = None
        self.properties_to_sell = list(player.properties)
        
        if player.is_ai:
            result = self._auto_sell_properties(player)
            if result == "paid":
                return self.handle_post_payment()
            return "end_turn"
        else:
            self.waiting_for_sell_decision = True
            label = "租金" if payment_type == "rent" else "土地税"
            self.add_message(f"现金不足！请选择一块地产出售以支付 ${amount} {label}")
            return "wait"
    
    def _perform_property_sale(self, player, prop):
        price = prop.property_price 
        player.add_cash(prop.property_price)
        prop.make_unowned()
        self.add_message(f"{player.name} 出售了 {prop.name}，获得 ${property_price}")
    
    def sell_property(self, player, tile_index):
        """出售指定的地产"""
        prop = self.board.get_tile(tile_index).property
        if prop and prop.owner == player:
            self._perform_property_sale(player, prop)
            if not player.is_ai:
                self.properties_to_sell = list(player.properties)
            return self.resolve_pending_payment()
        return None
    
    def _auto_sell_properties(self, player):
        while not player.can_afford(self.pending_payment_amount) and player.properties:
            prop_to_sell = AIPlayer.choose_property_to_sell(player)
            if not prop_to_sell:
                break
            self._perform_property_sale(player, prop_to_sell)
        return self.resolve_pending_payment()
    
    def resolve_pending_payment(self):
        """处理待支付的款项"""
        player = self.get_current_player()
        amount = self.pending_payment_amount
        receiver = self.pending_payment_receiver
        payment_type = self.pending_payment_type or "rent"
        
        if player.can_afford(amount):
            player.deduct_cash(amount)
            if receiver:
                receiver.add_cash(amount)
                if payment_type == "rent":
                    self.add_message(f"{player.name} 成功支付 ${amount} 租金给 {receiver.name}")
                else:
                    self.add_message(f"{player.name} 支付了 ${amount} 给 {receiver.name}")
            else:
                label = "土地税" if payment_type == "tax" else "费用"
                self.add_message(f"{player.name} 成功支付 ${amount} {label}")
            
            self.waiting_for_sell_decision = False
            self.properties_to_sell = []
            self.post_payment_action = self.pending_followup_action or "end_turn"
            self.pending_payment_amount = 0
            self.pending_payment_receiver = None
            self.pending_payment_type = None
            self.pending_followup_action = None
            return "paid"
        
        if not player.properties:
            label = "租金" if payment_type == "rent" else "土地税"
            self.add_message(f"{player.name} 已没有地产可卖，仍然无法支付{label}！")
            self.waiting_for_sell_decision = False
            self.properties_to_sell = []
            self.pending_payment_amount = 0
            self.pending_payment_receiver = None
            self.pending_payment_type = None
            self.pending_followup_action = None
            self.game_over = True
            self.winner = self.ai_player if player == self.human_player else self.human_player
            self.add_message("游戏结束！" + (self.winner.name if self.winner else "对手") + " 获胜！")
            return "bankrupt"
        
        # 仍需继续出售
        if player.is_ai:
            return self._auto_sell_properties(player)
        return "need_more"
    
    def handle_post_payment(self):
        """根据付款后续动作继续流程"""
        action = self.post_payment_action or "end_turn"
        self.post_payment_action = None
        if action == "continue_tile":
            result = self.process_tile_event()
        else:
            result = action
        self.cached_process_result = result
        return result

