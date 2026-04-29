import pygame
import math
import random

# ============================================
# Enemy type registry - factory pattern for extensibility
# ============================================
_enemy_types = {}

def register_enemy_type(name, factory_func):
    """Register a new enemy type. Call this to add new enemy variants."""
    _enemy_types[name] = factory_func

def get_available_types():
    """Return list of all registered enemy type names."""
    return list(_enemy_types.keys())

def create_enemy(type_name, world_pos, **overrides):
    """Create an enemy of the given type at world_pos with optional stat overrides."""
    factory = _enemy_types.get(type_name)
    if factory is None:
        raise ValueError(f"Unknown enemy type: {type_name}")
    return factory(world_pos, **overrides)

# ============================================
# Base Enemy class
# ============================================
class Enemy:
    """Base enemy with position, movement toward player, health, and rendering."""

    def __init__(self, world_pos, radius, speed, health, damage, color, points):
        """
        Initialize an enemy.

        Args:
            world_pos (pygame.Vector2): Spawn position in world coordinates.
            radius (int): Collision radius.
            speed (float): Movement speed in pixels/second.
            health (int): Starting health.
            damage (int): Damage dealt on player contact.
            color (tuple): RGB color tuple for rendering.
            points (int): Score value when killed.
        """
        self.pos = pygame.Vector2(world_pos)
        self.radius = radius
        self.speed = speed
        self.health = health
        self.max_health = health
        self.damage = damage
        self.color = color
        self.points = points

    def update(self, dt, player_pos):
        """Move toward the player (direct pursuit)."""
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * dt

    def take_damage(self, amount):
        """Reduce health by amount. Returns True if enemy is dead."""
        self.health -= amount
        return self.health <= 0

    def is_alive(self):
        """Check if enemy still has health."""
        return self.health > 0

    def draw(self, screen, camera_offset):
        """Render the enemy as a white diamond outline (matching user design)."""
        screen_pos = (self.pos.x - camera_offset.x, self.pos.y - camera_offset.y)
        r = self.radius
        diamond_points = [
            (screen_pos[0], screen_pos[1] - r),
            (screen_pos[0] + r * 0.7, screen_pos[1]),
            (screen_pos[0], screen_pos[1] + r),
            (screen_pos[0] - r * 0.7, screen_pos[1]),
        ]
        pygame.draw.polygon(screen, self.color, diamond_points, 2)

    def collides_with(self, other_pos, other_radius):
        """Check if another entity overlaps with this enemy."""
        return self.pos.distance_to(other_pos) < (self.radius + other_radius)

# ============================================
# Enemy type factories
# ============================================
def _make_basic(pos, **overrides):
    """Standard enemy: balanced speed and health."""
    stats = {"radius": 14, "speed": 120, "health": 2, "damage": 1, "color": (255, 80, 80), "points": 10}
    stats.update(overrides)
    return Enemy(pos, **stats)

def _make_fast(pos, **overrides):
    """Fast enemy: high speed, low health."""
    stats = {"radius": 10, "speed": 220, "health": 1, "damage": 1, "color": (80, 255, 80), "points": 15}
    stats.update(overrides)
    return Enemy(pos, **stats)

def _make_tank(pos, **overrides):
    """Tank enemy: slow, high health, high damage."""
    stats = {"radius": 22, "speed": 70, "health": 5, "damage": 2, "color": (80, 80, 255), "points": 25}
    stats.update(overrides)
    return Enemy(pos, **stats)

# Register default enemy types
register_enemy_type("basic", _make_basic)
register_enemy_type("fast", _make_fast)
register_enemy_type("tank", _make_tank)
