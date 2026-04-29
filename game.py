import pygame
import math
import random

from enemy import Enemy
from spawn_manager import SpawnManager
from difficulty_manager import DifficultyManager
from vfx_manager import VFXManager

# ============================================
# pygame setup - Pygame seadistus
# ============================================
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

# ============================================
# Map configuration - Kaardi seaded
# ============================================
WORLD_SIZE = 3000
MAP_INSET = 300

# Generate octagonal map vertices
center = WORLD_SIZE / 2
apothem = (WORLD_SIZE - 2 * MAP_INSET) / 2

map_vertices = []
for i in range(8):
    angle = math.radians(45 * i + 22.5)
    x = center + apothem * math.cos(angle)
    y = center + apothem * math.sin(angle)
    map_vertices.append((x, y))

# ============================================
# Camera - Kaamera jälgimine
# ============================================
camera_offset = pygame.Vector2(0, 0)

# ============================================
# Player settings - Mängija seaded
# ============================================
player_pos = pygame.Vector2(center, center)
player_radius = 15
player_angle = 0
target_angle = 0
rotation_speed = 8
player_max_health = 7
player_health = player_max_health
player_invulnerable_timer = 0.0
player_invulnerable_duration = 1.0
game_over = False

# ============================================
# Drift physics - Triivfüüsika
# ============================================
player_velocity = pygame.Vector2(0, 0)
player_acceleration = 1200      # Acceleration rate (pixels/s²)
player_drag = 4.0               # Friction coefficient (higher = less drift)
speed_power_multiplier = 1.7
speed_power_timer = 0.0

# ============================================
# Projectiles - Kuulid
# ============================================
projectiles = []
projectile_speed = 700
projectile_radius = 8

shoot_cooldown = 0.25           # Slower shooting speed
shoot_timer = 0
multi_shot_timer = 0.0
multi_shot_projectile_count = 3
multi_shot_spread = 18
rapid_fire_timer = 0.0
rapid_fire_multiplier = 2.0

# ============================================
# Power upid
# ============================================
powerups = []
powerup_radius = 13
powerup_drop_chance = 0.14
powerup_lifetime = 12.0
powerup_duration = 8.0
POWERUP_TYPES = {
    "multi_shot": {
        "color": (255, 210, 60),
        "label": "M",
    },
    "speed": {
        "color": (70, 220, 255),
        "label": "S",
    },
    "rapid_fire": {
        "color": (255, 110, 210),
        "label": "R",
    },
}

# ============================================
# Punktid
# ============================================
score = 0

# ============================================
# Enemy system - Vaenlase süsteem
# ============================================
enemies = []

# ============================================
# Time difficulty - Ajaline raskus
# ============================================
difficulty_manager = DifficultyManager()
spawn_manager = SpawnManager(map_vertices, (center, center), difficulty_manager)

# ============================================
# Visual effects - Visuaalsed efektid
# ============================================
vfx_manager = VFXManager()

# ============================================
# Player trail - Mängija jälg
# ============================================
TRAIL_LIFETIME = 0.5            # How long trail points last in seconds
TRAIL_INTERVAL = 0.02           # How often to record a trail point
trail_timer = 0
trail = []                      # List of (position, age) tuples

# ============================================
# Time system - Ajasüsteem
# ============================================
game_time = 0

# ============================================
# Utility functions - Abifunktsioonid
# ============================================

def point_in_polygon(point, vertices):
    """Check if a point is inside a polygon using ray casting algorithm."""
    x, y = point
    inside = False
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        if ((y1 > y) != (y2 > y)):
            xinters = (y - y1) * (x2 - x1) / (y2 - y1) + x1
            if xinters > x:
                inside = not inside
    return inside


def clamp_to_map(pos, vertices, radius):
    """Clamp player position to stay inside the map boundary."""
    if point_in_polygon((pos.x, pos.y), vertices):
        return pos

    # Find the closest point on any map edge
    min_dist = float('inf')
    closest = pos
    for i in range(len(vertices)):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % len(vertices)]
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            dist = math.hypot(pos.x - x1, pos.y - y1)
            if dist < min_dist:
                min_dist = dist
                closest = pygame.Vector2(x1, y1)
            continue
        t = max(0, min(1, ((pos.x - x1) * dx + (pos.y - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        dist = math.hypot(pos.x - proj_x, pos.y - proj_y)
        if dist < min_dist:
            min_dist = dist
            closest = pygame.Vector2(proj_x, proj_y)

    # Push player inside: dir_vec points from player to edge (inward)
    if min_dist > 0:
        dir_vec = pygame.Vector2(closest.x - pos.x, closest.y - pos.y).normalize()
        return closest + dir_vec * radius
    return pos


def spawn_powerup(world_pos):
    """Maybe create a power up at the given world position."""
    if random.random() > powerup_drop_chance:
        return

    powerup_type = random.choice(list(POWERUP_TYPES.keys()))
    powerups.append({
        "pos": pygame.Vector2(world_pos),
        "type": powerup_type,
        "age": 0.0,
    })


def create_projectile(spawn_pos, direction):
    """Create a projectile dictionary using the standard projectile speed."""
    return {
        "pos": pygame.Vector2(spawn_pos),
        "vel": direction * projectile_speed
    }


def apply_powerup(powerup_type):
    """Activate the collected power up."""
    global multi_shot_timer, speed_power_timer, rapid_fire_timer

    if powerup_type == "multi_shot":
        multi_shot_timer = powerup_duration
    elif powerup_type == "speed":
        speed_power_timer = powerup_duration
    elif powerup_type == "rapid_fire":
        rapid_fire_timer = powerup_duration


def draw_health_square(surface, x, y, size, filled):
    """Draw a small square health pip."""
    color = (255, 70, 95) if filled else (80, 80, 80)
    outline = (255, 120, 135) if filled else (120, 120, 120)
    rect = pygame.Rect(x, y, size, size)

    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, outline, rect, 2)


# ============================================
# Main game loop - Mängu tsükkel
# ============================================
while running:
    # poll for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    multi_shot_timer = max(0.0, multi_shot_timer - dt)
    speed_power_timer = max(0.0, speed_power_timer - dt)
    rapid_fire_timer = max(0.0, rapid_fire_timer - dt)
    player_invulnerable_timer = max(0.0, player_invulnerable_timer - dt)

    # ============================================
    # Player input - Mängija sisend
    # ============================================
    keys = pygame.key.get_pressed()
    input_dir = pygame.Vector2(0, 0)

    if not game_over and keys[pygame.K_w]:
        input_dir.y -= 1
    if not game_over and keys[pygame.K_s]:
        input_dir.y += 1
    if not game_over and keys[pygame.K_a]:
        input_dir.x -= 1
    if not game_over and keys[pygame.K_d]:
        input_dir.x += 1

    # ============================================
    # Drift movement - Liikumise triiv
    # ============================================
    if input_dir.length() > 0:
        input_dir = input_dir.normalize()
        current_acceleration = player_acceleration
        if speed_power_timer > 0:
            current_acceleration *= speed_power_multiplier
        player_velocity += input_dir * current_acceleration * dt

    # Apply drag (friction) - friction slows velocity
    player_velocity *= (1 - player_drag * dt)

    # Apply velocity to position
    player_pos += player_velocity * dt

    # Keep player inside the map
    player_pos = clamp_to_map(player_pos, map_vertices, player_radius)

    # Smooth rotation toward movement direction
    move_dir = player_velocity
    if move_dir.length() > 0:
        move_dir_normalized = move_dir.normalize()
        target_angle = pygame.Vector2(0, -1).angle_to(move_dir_normalized)

    angle_diff = target_angle - player_angle
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    if abs(angle_diff) > 0.5:
        player_angle += math.copysign(min(abs(angle_diff), rotation_speed * dt * 60), angle_diff)

    # ============================================
    # Shooting - Laskmine
    # ============================================
    shoot_timer -= dt
    mouse_buttons = pygame.mouse.get_pressed()

    if not game_over and mouse_buttons[0] and shoot_timer <= 0:
        world_mouse = pygame.Vector2(pygame.mouse.get_pos()) + camera_offset
        direction = world_mouse - player_pos

        if direction.length() != 0:
            direction = direction.normalize()

            # Shoot from the edge of the player - Kuuli laskmine äärest
            spawn_pos = player_pos + direction * (player_radius + projectile_radius)

            if multi_shot_timer > 0:
                middle_index = (multi_shot_projectile_count - 1) / 2
                for shot_index in range(multi_shot_projectile_count):
                    spread_angle = (shot_index - middle_index) * multi_shot_spread
                    shot_direction = direction.rotate(spread_angle)
                    projectiles.append(create_projectile(spawn_pos, shot_direction))
            else:
                projectiles.append(create_projectile(spawn_pos, direction))
            current_shoot_cooldown = shoot_cooldown
            if rapid_fire_timer > 0:
                current_shoot_cooldown /= rapid_fire_multiplier
            shoot_timer = current_shoot_cooldown

    # ============================================
    # Update projectiles - Kuulide uuendus
    # ============================================
    old_positions = []
    for projectile in projectiles:
        old_positions.append(pygame.Vector2(projectile["pos"]))
        projectile["pos"] += projectile["vel"] * dt

    # ============================================
    # Wall collision VFX - Seina tabamuse efekt
    # ============================================
    for i, projectile in enumerate(projectiles):
        if not point_in_polygon((projectile["pos"].x, projectile["pos"].y), map_vertices):
            # Spawn wall hit effect at the last valid position inside map
            vfx_manager.spawn_hit_effect(old_positions[i], "wall",
                                         direction=projectile["vel"].normalize())

    # Remove projectiles that leave the map
    projectiles = [
        p for p in projectiles
        if point_in_polygon((p["pos"].x, p["pos"].y), map_vertices)
    ]

    # ============================================
    # Enemy system - Vaenlase süsteem
    # ============================================
    # Spawn new enemy waves
    if game_over:
        new_enemies = []
    else:
        new_enemies = spawn_manager.update(dt, enemies, player_pos)

    # Apply difficulty speed scaling to new enemies
    speed_mult = difficulty_manager.get_enemy_speed_multiplier()
    health_bonus = difficulty_manager.get_enemy_health_bonus()
    for enemy_unit in new_enemies:
        enemy_unit.speed *= speed_mult
        enemy_unit.health += health_bonus
        enemy_unit.max_health = enemy_unit.health

    enemies.extend(new_enemies)

    # Update enemies - move toward player
    if not game_over:
        for enemy_unit in enemies:
            enemy_unit.update(dt, player_pos)

    # Enemy-player collision push - Vaenlase tõukumine
    # Push overlapping enemies away from player so they can't go inside
    for enemy_unit in enemies:
        dist = enemy_unit.pos.distance_to(player_pos)
        min_dist = enemy_unit.radius + player_radius
        if dist < min_dist and dist > 0:
            if not game_over and player_invulnerable_timer <= 0:
                player_health -= 1
                player_invulnerable_timer = player_invulnerable_duration
                if player_health <= 0:
                    player_health = 0
                    game_over = True
                    player_velocity.x = 0
                    player_velocity.y = 0

            push_dir = (enemy_unit.pos - player_pos).normalize()
            enemy_unit.pos = player_pos + push_dir * min_dist

    # ============================================
    # Collision detection - Kokkupõrge
    # ============================================
    bullets_to_remove = set()
    enemies_to_remove = set()

    for p_idx, projectile in enumerate(projectiles if not game_over else []):
        for e_idx, enemy_unit in enumerate(enemies):
            if e_idx in enemies_to_remove:
                continue
            if enemy_unit.collides_with(projectile["pos"], projectile_radius):
                bullets_to_remove.add(p_idx)
                if enemy_unit.take_damage(1):
                    enemies_to_remove.add(e_idx)
                    score += enemy_unit.score_value
                    spawn_powerup(enemy_unit.pos)
                    # Spawn enemy hit effect at enemy position
                    vfx_manager.spawn_hit_effect(
                        pygame.Vector2(enemy_unit.pos), "enemy"
                    )
                break  # Bullet can only hit one enemy

    # Remove hit bullets and dead enemies
    if bullets_to_remove:
        projectiles = [p for i, p in enumerate(projectiles) if i not in bullets_to_remove]
    if enemies_to_remove:
        enemies = [e for i, e in enumerate(enemies) if i not in enemies_to_remove]

    # ============================================
    # Power up collection
    # ============================================
    collected_powerups = set()
    for powerup_idx, powerup in enumerate(powerups if not game_over else []):
        powerup["age"] += dt
        if powerup["pos"].distance_to(player_pos) < player_radius + powerup_radius:
            apply_powerup(powerup["type"])
            collected_powerups.add(powerup_idx)
        elif powerup["age"] >= powerup_lifetime:
            collected_powerups.add(powerup_idx)

    if collected_powerups:
        powerups = [
            p for i, p in enumerate(powerups)
            if i not in collected_powerups
        ]

    # ============================================
    # Player trail - Mängija jälg
    # ============================================
    trail_timer += dt
    if trail_timer >= TRAIL_INTERVAL and move_dir.length() > 0:
        trail.append((pygame.Vector2(player_pos), 0))
        trail_timer = 0

    # Age trail points and remove expired ones
    trail = [(pos, age + dt) for pos, age in trail if age < TRAIL_LIFETIME]

    # ============================================
    # Camera follows the player - Kaamera jälgimine
    # ============================================
    camera_offset.x = player_pos.x - screen.get_width() / 2
    camera_offset.y = player_pos.y - screen.get_height() / 2

    # ============================================
    # Update time - Aja uuendus
    # ============================================
    if not game_over:
        game_time += dt
        difficulty_manager.update(dt)

    # ============================================
    # Update VFX - Efektide uuendus
    # ============================================
    vfx_manager.update(dt)

    # ============================================
    # Rendering - Renderdus
    # ============================================

    # fill the screen with black to wipe away anything from last frame
    screen.fill("black")

    # Draw map border - Kaardi piir
    pygame.draw.polygon(screen, "white", [(v[0] - camera_offset.x, v[1] - camera_offset.y) for v in map_vertices], 3)

    # Draw enemies - Vaenlase renderdus
    for enemy_unit in enemies:
        enemy_unit.draw(screen, camera_offset)

    # power upide ikoonid
    powerup_font = pygame.font.SysFont(None, 22)
    for powerup in powerups:
        config = POWERUP_TYPES[powerup["type"]]
        screen_pos = (
            int(powerup["pos"].x - camera_offset.x),
            int(powerup["pos"].y - camera_offset.y),
        )
        pulse = 1 + 0.12 * math.sin(pygame.time.get_ticks() * 0.008)
        radius = int(powerup_radius * pulse)
        pygame.draw.circle(screen, config["color"], screen_pos, radius, 2)
        label = powerup_font.render(config["label"], True, config["color"])
        label_pos = (
            screen_pos[0] - label.get_width() / 2,
            screen_pos[1] - label.get_height() / 2,
        )
        screen.blit(label, label_pos)

    # Draw player trail - Mängija jälg
    trail_radius = int(player_radius * 0.35)
    for pos, age in trail:
        screen_pos = (pos.x - camera_offset.x, pos.y - camera_offset.y)
        alpha = int(150 * (1 - age / TRAIL_LIFETIME))
        trail_surf = pygame.Surface((trail_radius * 2, trail_radius * 2))
        trail_surf.set_colorkey((0, 0, 0))
        trail_surf.set_alpha(alpha)
        pygame.draw.circle(trail_surf, (255, 255, 255), (trail_radius, trail_radius), trail_radius)
        screen.blit(trail_surf, (screen_pos[0] - trail_radius, screen_pos[1] - trail_radius))

    # Draw player arrow - Mängija nool
    arrow_points = [
        (0, -player_radius),
        (-player_radius * 0.5, player_radius * 0.3),
        (0, player_radius * 0.5),
        (player_radius * 0.5, player_radius * 0.3),
    ]

    arrow_surface = pygame.Surface((player_radius * 2, player_radius * 2), pygame.SRCALPHA)
    arrow_surface_points = [
        (p[0] + player_radius, p[1] + player_radius) for p in arrow_points
    ]
    arrow_alpha = 180
    if player_invulnerable_timer > 0 and int(pygame.time.get_ticks() / 120) % 2 == 0:
        arrow_alpha = 80
    pygame.draw.polygon(arrow_surface, (255, 255, 255, arrow_alpha), arrow_surface_points)
    rotated_arrow = pygame.transform.rotate(arrow_surface, -player_angle)
    screen_x = player_pos.x - camera_offset.x - rotated_arrow.get_width() / 2
    screen_y = player_pos.y - camera_offset.y - rotated_arrow.get_height() / 2
    screen.blit(rotated_arrow, (screen_x, screen_y))

    # Draw projectiles - Kuulide renderdus
    for projectile in projectiles:
        end_pos = projectile["pos"] + projectile["vel"].normalize() * 15
        start_screen = (projectile["pos"].x - camera_offset.x, projectile["pos"].y - camera_offset.y)
        end_screen = (end_pos.x - camera_offset.x, end_pos.y - camera_offset.y)
        pygame.draw.line(screen, "yellow", start_screen, end_screen, 3)

    # Draw VFX - Visuaalsed efektid
    vfx_manager.draw(screen, camera_offset)

    # Draw health squares
    health_size = 24
    health_gap = 8
    health_width = player_max_health * health_size + (player_max_health - 1) * health_gap
    health_x = screen.get_width() / 2 - health_width / 2
    for health_idx in range(player_max_health):
        square_x = int(health_x + health_idx * (health_size + health_gap))
        draw_health_square(screen, square_x, 10, health_size, health_idx < player_health)

    # Draw elapsed time - Aja kuvamine
    font = pygame.font.SysFont(None, 28)
    time_text = font.render(f"Time: {difficulty_manager.get_elapsed_time()}", True, (255, 255, 255))
    screen.blit(time_text, (10, 10))
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 38))

    active_powerups = []
    if multi_shot_timer > 0:
        active_powerups.append(f"Multi: {multi_shot_timer:.1f}s")
    if speed_power_timer > 0:
        active_powerups.append(f"Speed: {speed_power_timer:.1f}s")
    if rapid_fire_timer > 0:
        active_powerups.append(f"Fire Rate: {rapid_fire_timer:.1f}s")

    for idx, powerup_text in enumerate(active_powerups):
        rendered = font.render(powerup_text, True, (255, 255, 255))
        screen.blit(rendered, (10, 66 + idx * 26))

    if game_over:
        game_over_font = pygame.font.SysFont(None, 72)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 80, 80))
        score_final_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
        screen.blit(
            game_over_text,
            (
                screen.get_width() / 2 - game_over_text.get_width() / 2,
                screen.get_height() / 2 - game_over_text.get_height(),
            ),
        )
        screen.blit(
            score_final_text,
            (
                screen.get_width() / 2 - score_final_text.get_width() / 2,
                screen.get_height() / 2 + 10,
            ),
        )

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    dt = clock.tick(60) / 1000

pygame.quit()
