# -*- coding: utf-8 -*-
"""AI玩家决策逻辑"""

import random


class AIPlayer:
    """AI玩家决策器"""
    
    @staticmethod
    def decide_buy_property(player, property_obj):
        """
        决定是否购买地产
        策略：如果现金充足且价格合理，有70%概率购买
        """
        if not player.can_afford(property_obj.base_price):
            return False
            
        # 保留一定现金，不全部花光
        if player.cash - property_obj.base_price < 500:
            return False
            
        # 70%概率购买
        return random.random() > 0.3
        
    @staticmethod
    def choose_property_to_sell(player):
        """
        选择要出售的地产
        策略：出售价值最低的地产
        """
        if not player.properties:
            return None
        return min(player.properties, key=lambda prop: prop.property_price)

