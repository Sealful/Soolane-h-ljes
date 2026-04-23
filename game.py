import pygame
import math

# ============================================
# pygame setup
# ============================================
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

# ============================================
# Map configuration
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
# Camera
# ============================================
camera_offset = pygame.Vector2(0, 0)

# ============================================
# Player settings
# ============================================
player_pos = pygame.Vector2(center, center)
player_radius = 15
player_speed = 300
player_angle = 0
target_angle = 0
rotation_speed = 8

# ============================================
# Projectiles (kuulid)
# ============================================
projectiles = []
projectile_speed = 700
projectile_radius = 8

shoot_cooldown = 0.12
shoot_timer = 0

# ============================================
# Player trail (visual effect)
# ============================================
TRAIL_LIFETIME = 0.5  # how long trail points last in seconds
TRAIL_INTERVAL = 0.02  # how often to record a trail point
trail_timer = 0
trail = []  # list of (position, age) tuples

# ============================================
# Utility functions
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

    # Push player back inside by their radius
    if min_dist > 0:
        dir_vec = pygame.Vector2(closest.x - pos.x, closest.y - pos.y).normalize()
        return closest - dir_vec * radius
    return pos

# ============================================
# Main game loop
# ============================================
while running:
    # poll for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # WASD movement
    keys = pygame.key.get_pressed()
    move_dir = pygame.Vector2(0, 0)
    if keys[pygame.K_w]:
        move_dir.y -= 1
        player_pos.y -= player_speed * dt
    if keys[pygame.K_s]:
        move_dir.y += 1
        player_pos.y += player_speed * dt
    if keys[pygame.K_a]:
        move_dir.x -= 1
        player_pos.x -= player_speed * dt
    if keys[pygame.K_d]:
        move_dir.x += 1
        player_pos.x += player_speed * dt

    # Keep player inside the map
    player_pos = clamp_to_map(player_pos, map_vertices, player_radius)

    # Smooth rotation toward movement direction
    if move_dir.length() > 0:
        move_dir = move_dir.normalize()
        target_angle = pygame.Vector2(0, -1).angle_to(move_dir)

    angle_diff = target_angle - player_angle
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    if abs(angle_diff) > 0.5:
        player_angle += math.copysign(min(abs(angle_diff), rotation_speed * dt * 60), angle_diff)

    # Left click shooting (left clickiga laskmine)
    shoot_timer -= dt
    mouse_buttons = pygame.mouse.get_pressed()

    if mouse_buttons[0] and shoot_timer <= 0:  # left clicki hoidmine
        world_mouse = pygame.Vector2(pygame.mouse.get_pos()) + camera_offset
        direction = world_mouse - player_pos

        if direction.length() != 0:
            direction = direction.normalize()

            # Shoot from the edge of the player (kuuli laskmine selle tegelase äärest)
            spawn_pos = player_pos + direction * (player_radius + projectile_radius)

            projectile = {
                "pos": pygame.Vector2(spawn_pos),
                "vel": direction * projectile_speed
            }
            projectiles.append(projectile)
            shoot_timer = shoot_cooldown

    # Update projectiles (uuendab neid kuule)
    for projectile in projectiles:
        projectile["pos"] += projectile["vel"] * dt

    # Remove projectiles that leave the map (kustutab kuulid mis kaardilt välja lähevad)
    projectiles = [
        p for p in projectiles
        if point_in_polygon((p["pos"].x, p["pos"].y), map_vertices)
    ]

    # Update player trail (only record when moving)
    trail_timer += dt
    if trail_timer >= TRAIL_INTERVAL and move_dir.length() > 0:
        trail.append((pygame.Vector2(player_pos), 0))
        trail_timer = 0

    # Age trail points and remove expired ones
    trail = [(pos, age + dt) for pos, age in trail if age < TRAIL_LIFETIME]

    # Camera follows the player
    camera_offset.x = player_pos.x - screen.get_width() / 2
    camera_offset.y = player_pos.y - screen.get_height() / 2

    # ============================================
    # Rendering
    # ============================================

    # fill the screen with black to wipe away anything from last frame
    screen.fill("black")

    # Draw map border
    pygame.draw.polygon(screen, "white", [(v[0] - camera_offset.x, v[1] - camera_offset.y) for v in map_vertices], 3)

    # Draw player trail (visual effect - small fading circles)
    trail_radius = int(player_radius * 0.35)
    for pos, age in trail:
        screen_pos = (pos.x - camera_offset.x, pos.y - camera_offset.y)
        alpha = int(150 * (1 - age / TRAIL_LIFETIME))
        trail_surf = pygame.Surface((trail_radius * 2, trail_radius * 2))
        trail_surf.set_colorkey((0, 0, 0))
        trail_surf.set_alpha(alpha)
        pygame.draw.circle(trail_surf, (255, 255, 255), (trail_radius, trail_radius), trail_radius)
        screen.blit(trail_surf, (screen_pos[0] - trail_radius, screen_pos[1] - trail_radius))

    # Draw player arrow (tegeline)
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
    pygame.draw.polygon(arrow_surface, (255, 255, 255, 180), arrow_surface_points)
    rotated_arrow = pygame.transform.rotate(arrow_surface, -player_angle)
    screen_x = player_pos.x - camera_offset.x - rotated_arrow.get_width() / 2
    screen_y = player_pos.y - camera_offset.y - rotated_arrow.get_height() / 2
    screen.blit(rotated_arrow, (screen_x, screen_y))

    # Draw projectiles (kuulid)
    for projectile in projectiles:
        end_pos = projectile["pos"] + projectile["vel"].normalize() * 15
        start_screen = (projectile["pos"].x - camera_offset.x, projectile["pos"].y - camera_offset.y)
        end_screen = (end_pos.x - camera_offset.x, end_pos.y - camera_offset.y)
        pygame.draw.line(screen, "yellow", start_screen, end_screen, 3)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    dt = clock.tick(60) / 1000

pygame.quit()
