# -*- coding: utf-8 -*-
"""地产类定义"""

from config import (
    PROPERTY_MAX_LEVEL, 
    PROPERTY_LEVEL_MULTIPLIER,
    PROPERTY_UPGRADE_RATE, 
    PROPERTY_MAINTENANCE_RATE,
    PROPERTY_INITIAL_RENT_RATE
)


class Property:
    """地产类"""
    
    def __init__(self, name, base_price, rent_rate, tile_index):
        self.name = name
        self.base_price = base_price
        self.rent_rate = rent_rate if rent_rate > 0 else PROPERTY_INITIAL_RENT_RATE
        self.tile_index = tile_index
        self.owner = None
        
        # 等级系统
        self.level = 0
        
        # 当前价格（受等级和CPI影响）
        self.property_price = base_price
        
    def has_owner(self):
        """是否有主人"""
        return self.owner is not None
        
    def transfer_ownership(self, new_owner, old_owner=None):
        """转移所有权"""
        if old_owner is None:
            old_owner = self.owner
            
        if old_owner and self in old_owner.properties:
            old_owner.properties.remove(self)
            
        if new_owner:
            new_owner.properties.append(self)
            
        self.owner = new_owner

    def make_unowned(self):
        """使地产变为无主"""
        if self.owner:
            if self in self.owner.properties:
                self.owner.properties.remove(self)
            self.owner = None
        self.level = 0

    def update_property_price(self, cpi):
        """根据等级和CPI更新地产价格"""
        level_factor = 1.0 + (self.level * PROPERTY_LEVEL_MULTIPLIER)
        cpi_factor = 1.0 + cpi

        self.property_price = int(self.property_price * cpi_factor)*(1+0.2)**self.level

    def get_rent(self, cpi):
        """计算当前租金"""
        self.update_property_price(cpi)
        return int(self.property_price * self.rent_rate)

    def can_upgrade(self):
        """是否可以升级"""
        return self.level < PROPERTY_MAX_LEVEL and self.owner is not None

    def get_upgrade_cost(self, cpi):
        """计算升级成本"""
        cpi_factor = 1.0 + cpi
        return int(self.property_price * PROPERTY_UPGRADE_RATE * cpi_factor)

    def upgrade(self):
        """升级地产"""
        if self.can_upgrade():
            self.level += 1
            return True
        return False

    def get_maintenance_cost(self, cpi):
        """计算维护成本"""
        if self.owner is None or self.level == 0:
            return 0
        cpi_factor = 1.0 + cpi
        return int(self.property_price * PROPERTY_MAINTENANCE_RATE * cpi_factor)

