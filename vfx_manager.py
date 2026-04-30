import pygame
import random
import math

# ============================================
# Effect type registry - Efektide register
# ============================================

# Registry for effect type configurations - allows adding new effects
# without modifying core VFX logic. Future hooks - Tulevikuks.
_effect_types = {}


def register_effect_type(name, config):
    """Register a new visual effect type - Uue efekt registreerimine.

    Args:
        name (str): Unique identifier for the effect type.
        config (dict): Effect configuration with keys:
            - particle_count (int): Number of particles per effect
            - colors (list): List of RGB color tuples to pick from
            - speed_min (float): Minimum particle speed
            - speed_max (float): Maximum particle speed
            - spread (float): Angular spread in degrees (360 = full circle)
            - lifetime_min (float): Minimum particle lifetime in seconds
            - lifetime_max (float): Maximum particle lifetime in seconds
            - size_min (int): Minimum particle radius
            - size_max (int): Maximum particle radius
    """
    _effect_types[name] = config


def get_effect_types():
    """Return list of all registered effect type names."""
    return list(_effect_types.keys())


# ============================================
# Default effect configurations - Vaike efektid
# ============================================

# Enemy hit effect - Vaenlase tabamus (red/orange burst)
register_effect_type("enemy", {
    "particle_count": 12,
    "colors": [(255, 80, 40), (255, 160, 40), (255, 220, 80), (200, 50, 30)],
    "speed_min": 60.0,
    "speed_max": 200.0,
    "spread": 360.0,
    "lifetime_min": 0.2,
    "lifetime_max": 0.5,
    "size_min": 2,
    "size_max": 5,
})

# Wall hit effect - Seina tabamus (white/blue sparks)
register_effect_type("wall", {
    "particle_count": 8,
    "colors": [(200, 220, 255), (150, 180, 255), (255, 255, 255), (100, 140, 255)],
    "speed_min": 40.0,
    "speed_max": 150.0,
    "spread": 180.0,
    "lifetime_min": 0.15,
    "lifetime_max": 0.35,
    "size_min": 1,
    "size_max": 3,
})

# ============================================
# Particle class - Osakeste klass
# ============================================


class Particle:
    """Single visual effect particle - Üks osake.

    Tracks position, velocity, lifetime, color, and size for rendering.
    """

    def __init__(self, pos, vel, lifetime, color, size):
        """Initialize a particle - Osakese loomine.

        Args:
            pos (pygame.Vector2): World position.
            vel (pygame.Vector2): Velocity vector.
            lifetime (float): Total lifetime in seconds.
            color (tuple): RGB color tuple.
            size (int): Particle radius in pixels.
        """
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size

    def update(self, dt):
        """Advance particle state by delta time - Osakese uuendus.

        Args:
            dt (float): Seconds since last frame.
        """
        self.pos += self.vel * dt
        self.lifetime -= dt

    def is_alive(self):
        """Check if particle is still active.

        Returns:
            bool: True if particle has remaining lifetime.
        """
        return self.lifetime > 0

    def get_alpha(self):
        """Get current alpha (opacity) based on remaining lifetime.

        Returns:
            int: Alpha value from 0 (dead) to 255 (fresh).
        """
        ratio = self.lifetime / self.max_lifetime
        return int(255 * ratio)


# ============================================
# VFX Manager - Visuaalsed efektid
# ============================================


class VFXManager:
    """Manages all active particle effects - Efektide haldur.

    Spawns, updates, and renders particle effects at world positions.
    Uses the effect type registry for extensible effect definitions.
    """

    def __init__(self):
        """Initialize VFX manager with empty particle pool."""
        self.particles = []

    def spawn_hit_effect(self, world_pos, effect_type, direction=None):
        """Spawn a hit effect at the given world position - Tabamuse efekt.

        Args:
            world_pos (pygame.Vector2): World coordinates for effect origin.
            effect_type (str): Registered effect type name (e.g. "enemy", "wall").
            direction (pygame.Vector2, optional): Direction to bias particle spread.
                Used for wall effects to spread away from wall surface.
        """
        config = _effect_types.get(effect_type)
        if config is None:
            raise ValueError(f"Unknown effect type: {effect_type}")

        base_angle = 0.0
        if direction is not None and direction.length() > 0:
            base_angle = math.degrees(math.atan2(-direction.y, direction.x))

        for _ in range(config["particle_count"]):
            # Random angle within spread
            angle_offset = random.uniform(-config["spread"] / 2, config["spread"] / 2)
            angle = math.radians(base_angle + angle_offset)

            # Random speed
            speed = random.uniform(config["speed_min"], config["speed_max"])
            vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)

            # Random lifetime and size
            lifetime = random.uniform(config["lifetime_min"], config["lifetime_max"])
            size = random.randint(config["size_min"], config["size_max"])
            color = random.choice(config["colors"])

            particle = Particle(world_pos, vel, lifetime, color, size)
            self.particles.append(particle)

    def update(self, dt):
        """Update all active particles - Osakeste uuendus.

        Removes expired particles and advances remaining ones.

        Args:
            dt (float): Seconds since last frame.
        """
        for particle in self.particles:
            particle.update(dt)

        # Remove dead particles
        self.particles = [p for p in self.particles if p.is_alive()]

    def draw(self, screen, camera_offset):
        """Render all active particles - Osakeste renderdus.

        Args:
            screen (pygame.Surface): Target display surface.
            camera_offset (pygame.Vector2): World-to-screen offset.
        """
        for particle in self.particles:
            screen_pos = (
                particle.pos.x - camera_offset.x,
                particle.pos.y - camera_offset.y,
            )
            alpha = particle.get_alpha()

            # Create per-particle surface for alpha blending
            size = particle.size
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color_with_alpha = (*particle.color, alpha)
            pygame.draw.circle(surf, color_with_alpha, (size, size), size)
            screen.blit(surf, (screen_pos[0] - size, screen_pos[1] - size))

    def get_active_count(self):
        """Return number of currently active particles.

        Returns:
            int: Count of particles still alive.
        """
        return len(self.particles)
