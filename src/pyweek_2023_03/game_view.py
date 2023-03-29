"""Game View"""


import arcade

from .assets import get_tile_map_path
from .constants import (
    DASH_MOVE_IMPULSE,
    DEFAULT_DAMPING,
    GRAVITY,
    KEYMAP_DICT,
    PLAYER_FRICTION,
    PLAYER_JUMP_IMPULSE,
    PLAYER_MASS,
    PLAYER_MAX_HORIZONTAL_SPEED,
    PLAYER_MAX_VERTICAL_SPEED,
    PLAYER_MOVE_FORCE_IN_AIR,
    PLAYER_MOVE_FORCE_ON_GROUND,
    TILE_SCALING,
)
from .handlers import player_hits_enemy
from .sprites.enemy import DemoEnemy
from .sprites.player import Player


# pylint: disable=too-many-instance-attributes
class GameView(arcade.View):
    """Main application class."""

    def __init__(self):
        # Call the parent class and set up the window
        super().__init__()

        # Our TileMap Object
        self.tile_map = None

        # Our Scene Object
        self.scene = None

        # Separate variable that holds the player sprite
        self.player = None

        # Our physics engine
        self.physics_engine = None

        # A Camera that can be used for scrolling the screen
        self.camera_sprites = None

        # A non-scrolling camera that can be used to draw GUI elements
        self.camera_gui = None

        # Keep track of the score
        self.score = 0

        # What key is pressed down?
        self.left_key_down = False
        self.right_key_down = False

    def on_show_view(self):
        arcade.set_background_color(arcade.csscolor.BLACK)
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        # Setup the Cameras
        self.camera_sprites = arcade.Camera(self.window.width, self.window.height)
        self.camera_gui = arcade.Camera(self.window.width, self.window.height)

        self.physics_engine = arcade.PymunkPhysicsEngine((0, -GRAVITY), damping=DEFAULT_DAMPING)

        # Name of map file to load

        # Layer specific options are defined based on Layer names in a dictionary
        # Doing this will make the SpriteList for the platforms layer
        # use spatial hashing for detection.
        layer_options = {
            "Blocks": {
                "use_spatial_hash": True,
            }
        }

        # Read in the tiled map
        with get_tile_map_path("inf_demo") as map_path:
            self.tile_map = arcade.load_tilemap(map_path, TILE_SCALING, layer_options)

        # Initialize Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        for spawner in self.scene.get_sprite_list("Spawners"):
            entity_id = spawner.properties["tile_id"]
            if entity_id == 0:
                self.player = Player(spawner.bottom, spawner.left, "player/realistic_player", 100, 30, None, self)
                self.scene.add_sprite("Player", self.player)
                self.player.setup_player()
            elif entity_id == 1:
                enemy = DemoEnemy(spawner.bottom, spawner.left, self)
                enemy.generate_available_spaces(self.scene["Blocks"])
                self.scene.add_sprite("Enemy", enemy)
                self.physics_engine.add_sprite(
                    enemy,
                    friction=PLAYER_FRICTION,
                    mass=PLAYER_MASS,
                    moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                    collision_type="enemy",
                    damping=1.0,
                    max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED / 2,
                    max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED,
                )

                self.physics_engine.add_collision_handler(
                    "player",
                    "enemy",
                    player_hits_enemy,
                )

        self.scene.remove_sprite_list_by_name("Spawners")

        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # Keep track of the score
        self.score = 0

        self.physics_engine.add_sprite(
            self.player,
            friction=PLAYER_FRICTION,
            mass=PLAYER_MASS,
            moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
            collision_type="player",
            max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
            max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED,
        )

        self.physics_engine.add_sprite_list(
            self.scene["Blocks"],
            body_type=1,
            friction=1,
            damping=DEFAULT_DAMPING,
            collision_type="block",
        )

    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        # Activate the game camera
        self.camera_sprites.use()

        # Draw our Scene
        # Note, if you a want pixelated look, add pixelated=True to the parameters
        self.scene.draw()

        # Activate the GUI camera before drawing GUI elements
        self.camera_gui.use()

        self.player.update_animation()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            start_x=10,
            start_y=10,
            color=arcade.csscolor.WHITE,
            font_size=18,
        )

    def update_player_speed(self):
        """Calculate speed based on the keys pressed"""
        is_on_ground = self.physics_engine.is_on_ground(self.player)
        # Update player forces based on keys pressed
        if self.left_key_down and not self.right_key_down:
            # Create a force to the left. Apply it.
            if is_on_ground:
                force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)

            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player, 0)
            self.player.is_facing_right = False
        elif self.right_key_down and not self.left_key_down:
            # Create a force to the right. Apply it.
            if is_on_ground:
                force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)

            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player, 0)
            self.player.is_facing_right = True
        else:
            # Player's feet are not moving. Therefore, up the friction so we stop.
            self.physics_engine.set_friction(self.player, 1.0)

    def on_key_press(self, symbol, modifiers):
        """Called whenever a key is pressed."""
        if symbol in KEYMAP_DICT["Jump"]:
            if self.physics_engine.is_on_ground(self.player):
                impulse = (0, PLAYER_JUMP_IMPULSE)
                self.physics_engine.apply_impulse(self.player, impulse)
            self.update_player_speed()
        elif symbol in KEYMAP_DICT["Left"]:
            self.left_key_down = True
            self.update_player_speed()
        elif symbol in KEYMAP_DICT["Right"]:
            self.right_key_down = True
            self.update_player_speed()
        elif symbol in KEYMAP_DICT["Dash"]:
            if self.player.dashes:
                impulse = (DASH_MOVE_IMPULSE, 0) if self.player.is_facing_right else (-DASH_MOVE_IMPULSE, 0)
                self.physics_engine.apply_impulse(self.player, impulse)
                self.player.use_dash()
                self.update_player_speed()

    # pylint: disable=unused-argument
    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""
        if key in KEYMAP_DICT["Left"]:
            self.left_key_down = False
            self.update_player_speed()
        elif key in KEYMAP_DICT["Right"]:
            self.right_key_down = False
            self.update_player_speed()

    def center_camera_to_player(self):
        """Centers the camera to the player"""
        # Find where player is, then calculate lower left corner from that
        screen_center_x = self.player.center_x - (self.camera_sprites.viewport_width / 2)
        screen_center_y = self.player.center_y - (self.camera_sprites.viewport_height / 2)

        # Set some limits on how far we scroll
        screen_center_x = max(screen_center_x, 0)
        screen_center_y = max(screen_center_y, 0)

        # Here's our center, move to it
        player_centered = screen_center_x, screen_center_y
        self.camera_sprites.move_to(player_centered)

    def update_enemies(self):
        """Updates enemies"""
        for enemy in self.scene["Enemy"]:
            if enemy.look_for(self.player, self.scene["Blocks"]):
                enemy.notice_player()
                enemy.target_position = self.player.left, self.player.bottom

            if enemy.mode == 1:
                enemy.target_position = self.player.left, self.player.bottom
                enemy.moving = True
                pos_x = self.player.left - enemy.left
                enemy.direction = abs(pos_x) / pos_x

            if enemy.moving:
                if self.physics_engine.is_on_ground(enemy):
                    force = (7_000 * enemy.direction, 0)
                else:
                    force = (1_000 * enemy.direction, 0)
                self.physics_engine.set_friction(enemy, 0)
                self.physics_engine.apply_force(enemy, force)

                if enemy.target_position[1] > enemy.position[1] and self.physics_engine.is_on_ground(enemy):
                    impulse = (0, PLAYER_JUMP_IMPULSE)
                    self.physics_engine.apply_impulse(enemy, impulse)

                if enemy.direction == 1:
                    cond = enemy.position[0] > enemy.target_position[0]
                else:
                    cond = enemy.position[0] < enemy.target_position[0]
                if cond and enemy.mode != 1:
                    self.physics_engine.set_friction(enemy, 1.0)
                    enemy.cur_movement_cd = enemy.movement_cd
                    enemy.moving = False

    def on_update(self, delta_time):
        """Movement and game logic"""

        # Move the player with the physics engine
        self.physics_engine.step()

        # Position the camera
        self.center_camera_to_player()

        self.player.on_update(delta_time)

        self.update_enemies()

    def on_resize(self, width, height):
        """Resize window"""
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))