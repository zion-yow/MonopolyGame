# -*- coding: utf-8 -*-
"""玩家类定义"""


class Player:
    """玩家类"""
    
    def __init__(self, name, cash, is_ai=False, color=(100, 150, 255)):
        self.name = name
        self.cash = cash
        self.position = 0
        self.properties = []
        self.is_ai = is_ai
        self.color = color
        
    def get_total_wealth(self):
        """计算总财富"""
        wealth = self.cash
        for prop in self.properties:
            wealth += prop.price
        return wealth
        
    def add_cash(self, amount):
        """增加现金"""
        self.cash += amount
        
    def deduct_cash(self, amount):
        """扣除现金"""
        if self.cash >= amount:
            self.cash -= amount
            return True
        return False
        
    def can_afford(self, amount):
        """能否支付"""
        return self.cash >= amount
        
    def move(self, steps, total_tiles):
        """移动"""
        old_position = self.position
        self.position = (self.position + steps) % total_tiles
        return self.position < old_position  # 是否经过起点

