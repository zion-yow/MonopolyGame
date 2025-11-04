# -*- coding: utf-8 -*-
"""地产类定义"""


class Property:
    """地产类"""
    
    def __init__(self, name, price, rent, tile_index):
        self.name = name
        self.price = price
        self.rent = rent
        self.tile_index = tile_index
        self.owner = None
        
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

