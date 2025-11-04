# -*- coding: utf-8 -*-
"""地图管理器"""

import math
import random
from models.tile import Tile, TileType
from models.property import Property
from config import *


class BoardManager:
    """地图管理器"""
    
    def __init__(self, total_tiles):
        self.total_tiles = total_tiles
        self.tiles = []
        self._generate_board()
        
    def _generate_board(self):
        """生成地图"""
        # 定义地块类型及其权重
        tile_type_options = [TileType.PROPERTY, TileType.CHANCE, TileType.TAX]
        weights = [0.7, 0.2, 0.1]

        for i in range(self.total_tiles):
            # 计算地块位置（圆形排列）
            angle = (360 / self.total_tiles) * i
            radian = math.radians(angle)
            x = BOARD_CENTER_X + math.cos(radian) * BOARD_RADIUS
            y = BOARD_CENTER_Y + math.sin(radian) * BOARD_RADIUS
            
            # 确定地块类型
            if i == 0:
                tile_type = TileType.START
            else:
                # 根据权重随机选择地块类型
                tile_type = random.choices(tile_type_options, weights, k=1)[0]
                
            tile = Tile(i, tile_type, (x, y))
            
            # 如果是地产，创建地产对象
            if tile_type == TileType.PROPERTY:
                base_price = 500 + i * 100
                property_obj = Property(
                    f"地产{i}",
                    base_price,
                    base_price // 5,
                    i
                )
                tile.property = property_obj
                
            self.tiles.append(tile)
            
    def get_tile(self, index):
        """获取指定索引的地块"""
        return self.tiles[index]
        
    def get_player_position(self, tile_index, is_ai=False):
        """获取玩家在地块上的显示位置"""
        tile = self.tiles[tile_index]
        x, y = tile.position
        # 移除偏移，使玩家居中

        # ai向右偏移15
        if is_ai:
            x += 15
        # 玩家向左偏移15
        else:
            x -= 15
        return (x, y)

