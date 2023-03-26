import arcade

from .. import constants
from ..assets import get_sprite_path


class Character(arcade.Sprite):
    """Base enemy class from which the various enemy types are made"""

    def __init__(self, bottom, left, sprite: str, health: int, speed: int, weapon):
        sprite_type, sprite_name = sprite.split("/")
        print(sprite_type, sprite_name)
        with get_sprite_path(sprite_type, sprite_name) as sprite_path:
            super().__init__(sprite_path, constants.CHARACTER_SCALING)
            
        self.bottom = bottom
        self.left = left

        self.health = health
        self.speed = speed
        self.weapon = weapon