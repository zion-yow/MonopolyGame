# -*- coding: utf-8 -*-
"""地块类定义"""

from enum import Enum


class TileType(Enum):
    """地块类型枚举"""
    START = "起点"
    PROPERTY = "地产"
    CHANCE = "机会"
    TAX = "税收"
    EMPTY = "空地"


class Tile:
    """地块类"""
    
    def __init__(self, index, tile_type, position):
        self.index = index
        self.tile_type = tile_type
        self.position = position  # (x, y)坐标
        self.property = None      # 关联的地产对象
        
    def get_color(self):
        """根据类型返回地块颜色"""
        from config import WHITE, GREEN, YELLOW, GRAY, LIGHT_BLUE, LIGHT_RED
        
        if self.tile_type == TileType.START:
            return GREEN
        elif self.tile_type == TileType.CHANCE:
            return YELLOW
        elif self.tile_type == TileType.TAX:
            return GRAY
        elif self.tile_type == TileType.PROPERTY:
            if self.property and self.property.owner:
                # 根据拥有者返回不同颜色
                return LIGHT_BLUE if self.property.owner.name == "玩家" else LIGHT_RED
            return WHITE
        return WHITE

