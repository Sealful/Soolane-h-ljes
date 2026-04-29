import random
import math
import pygame
import enemy

# ============================================
# Spawn configuration - Tekitamise seaded
# ============================================
SPAWN_INTERVAL = 2.0        # Seconds between spawn waves
MAX_ENEMIES = 20            # Maximum concurrent enemies on map
WAVE_SIZE_MIN = 1           # Minimum enemies per wave
WAVE_SIZE_MAX = 4           # Maximum enemies per wave
SPAWN_JITTER = 80           # Random offset along map edge (pixels)
SPREAD_RADIUS = 30          # How far wave members scatter from spawn point

# Future hooks (unused now, available for later expansion) - Tuleviku konksud:
# directional_bias = False    # Spawn away from player movement direction

class SpawnManager:
    """Manages randomized enemy spawning along the map border - Tekitamine."""

    def __init__(self, map_vertices, world_center, difficulty_manager=None):
        """
        Initialize the spawn manager.

        Args:
            map_vertices (list): List of (x, y) tuples defining the map polygon.
            world_center (pygame.Vector2): Center point of the map.
            difficulty_manager (DifficultyManager, optional): Difficulty scaling.
                Falls back to static config if not provided.
        """
        self.map_vertices = map_vertices
        self.world_center = pygame.Vector2(world_center)
        self.spawn_timer = 0.0
        self.difficulty_manager = difficulty_manager

    def update(self, dt, current_enemies, player_pos):
        """
        Check if it's time to spawn a new wave and do so if conditions are met.

        Args:
            dt (float): Delta time since last frame.
            current_enemies (list): Current list of alive enemies.
            player_pos (pygame.Vector2): Player's current world position.

        Returns:
            list: Newly spawned enemies this frame (may be empty).
        """
        new_enemies = []
        self.spawn_timer -= dt

        if self.spawn_timer > 0:
            return new_enemies

        if len(current_enemies) >= MAX_ENEMIES:
            return new_enemies

        # Use difficulty manager for spawn interval if available - Raskuse skaala
        if self.difficulty_manager is not None:
            self.spawn_timer = self.difficulty_manager.get_spawn_interval()
        else:
            self.spawn_timer = SPAWN_INTERVAL

        wave_size = random.randint(WAVE_SIZE_MIN, WAVE_SIZE_MAX)

        for _ in range(wave_size):
            if len(current_enemies) + len(new_enemies) >= MAX_ENEMIES:
                break

            spawn_pos = self._get_random_spawn_point()
            type_name = self._select_enemy_type()
            new_enemy = enemy.create_enemy(type_name, spawn_pos)
            new_enemies.append(new_enemy)

        return new_enemies

    def _select_enemy_type(self):
        """Select enemy type based on difficulty weighting - Tüüpide valik.

        Uses difficulty manager weights if available, otherwise random.

        Returns:
            str: Enemy type name.
        """
        available_types = enemy.get_available_types()

        if self.difficulty_manager is not None:
            weights = self.difficulty_manager.get_type_weights()
            # Map weights to available types in order
            type_map = ["basic", "fast", "tank"]
            weighted_types = []
            for type_name, weight in zip(type_map, weights):
                weighted_types.extend([type_name] * int(weight * 100))
            return random.choice(weighted_types)
        else:
            return random.choice(available_types)

    def _get_random_spawn_point(self):
        """
        Generate a random spawn position along the map border.

        Uses an angular method: pick random angle from center, find edge
        intersection, add jitter, offset outside the map.

        Returns:
            pygame.Vector2: World position just outside the map boundary.
        """
        angle = random.uniform(0, 360)
        ray_dir = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle)))

        # Find intersection with map border
        best_dist = float('inf')
        best_point = None

        for i in range(len(self.map_vertices)):
            v1 = pygame.Vector2(self.map_vertices[i])
            v2 = pygame.Vector2(self.map_vertices[(i + 1) % len(self.map_vertices)])

            intersect = self._ray_segment_intersect(self.world_center, ray_dir, v1, v2)
            if intersect is not None:
                dist = self.world_center.distance_to(intersect)
                if dist < best_dist:
                    best_dist = dist
                    best_point = intersect

        if best_point is None:
            best_point = pygame.Vector2(self.world_center) + ray_dir * 500

        # Add jitter along the edge segment
        jitter_amount = random.uniform(-SPAWN_JITTER, SPAWN_JITTER)
        edge_dir = self._get_edge_direction(best_point)
        jittered_point = best_point + edge_dir * jitter_amount

        # Offset outside the map by a small amount
        outward_dir = (jittered_point - self.world_center).normalize()
        spawn_point = jittered_point + outward_dir * 40

        return pygame.Vector2(spawn_point)

    def _ray_segment_intersect(self, origin, direction, seg_a, seg_b):
        """
        Find intersection point between a ray and a line segment.

        Args:
            origin (pygame.Vector2): Ray origin point.
            direction (pygame.Vector2): Ray direction (should be normalized).
            seg_a (pygame.Vector2): Segment start point.
            seg_b (pygame.Vector2): Segment end point.

        Returns:
            pygame.Vector2 or None: Intersection point, or None if no intersection.
        """
        edge = seg_b - seg_a
        edge_len_sq = edge.length_squared()

        if edge_len_sq == 0:
            return None

        t = edge.dot(direction)
        u = edge.dot(origin - seg_a)

        denominator = edge.dot(direction)
        if abs(denominator) < 0.0001:
            return None

        t = ((seg_a.x - origin.x) * direction.x + (seg_a.y - origin.y) * direction.y) / denominator
        # Use parametric form
        # Ray: origin + t * direction
        # Segment: seg_a + u * edge
        cross_val = direction.x * edge.y - direction.y * edge.x
        if abs(cross_val) < 0.0001:
            return None  # Parallel

        t_param = ((seg_a.x - origin.x) * edge.y - (seg_a.y - origin.y) * edge.x) / cross_val
        u_param = ((seg_a.x - origin.x) * direction.y - (seg_a.y - origin.y) * direction.x) / cross_val

        if t_param > 0 and 0 <= u_param <= 1:
            return origin + direction * t_param

        return None

    def _get_edge_direction(self, point):
        """
        Get the direction along the map edge at the given point.

        Returns a normalized vector tangent to the nearest edge segment.

        Args:
            point (pygame.Vector2): Point on the map border.

        Returns:
            pygame.Vector2: Normalized edge direction.
        """
        min_dist = float('inf')
        best_dir = pygame.Vector2(1, 0)

        for i in range(len(self.map_vertices)):
            v1 = pygame.Vector2(self.map_vertices[i])
            v2 = pygame.Vector2(self.map_vertices[(i + 1) % len(self.map_vertices)])
            edge = v2 - v1
            edge_len = edge.length()
            if edge_len == 0:
                continue

            t = max(0, min(1, (point - v1).dot(edge) / (edge_len * edge_len)))
            closest = v1 + edge * t
            dist = point.distance_to(closest)

            if dist < min_dist:
                min_dist = dist
                best_dir = edge.normalize()

        return best_dir
