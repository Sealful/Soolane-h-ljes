import pygame

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
player_radius = 40
player_speed = 300

projectiles = []
projectile_speed = 700
projectile_radius = 8

shoot_cooldown = 0.12
shoot_timer = 0

while running:
    # poll for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_pos.y -= player_speed * dt
    if keys[pygame.K_s]:
        player_pos.y += player_speed * dt
    if keys[pygame.K_a]:
        player_pos.x -= player_speed * dt
    if keys[pygame.K_d]:
        player_pos.x += player_speed * dt

    # left clickiga laskmine
    shoot_timer -= dt
    mouse_buttons = pygame.mouse.get_pressed()

    if mouse_buttons[0] and shoot_timer <= 0:  # left clicki hoidmine
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        direction = mouse_pos - player_pos

        if direction.length() != 0:
            direction = direction.normalize()

            # kuuli laskmine selle tegelase äärest
            spawn_pos = player_pos + direction * (player_radius + projectile_radius)

            projectile = {
                "pos": pygame.Vector2(spawn_pos),
                "vel": direction * projectile_speed
            }
            projectiles.append(projectile)
            shoot_timer = shoot_cooldown

    # uuendab neid kuule
    for projectile in projectiles:
        projectile["pos"] += projectile["vel"] * dt

    # kustutab kuulid mis ekraanist välja lähgevad
    projectiles = [
        p for p in projectiles
        if 0 <= p["pos"].x <= screen.get_width()
        and 0 <= p["pos"].y <= screen.get_height()
    ]

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    mouse_pos = pygame.mouse.get_pos()
    angle = pygame.math.Vector2(mouse_pos) - player_pos
    angle = angle.angle_to(pygame.Vector2(0, -1))

    arrow_points = [
        (0, -player_radius),
        (-player_radius * 0.6, player_radius * 0.5),
        (0, player_radius * 0.3),
        (player_radius * 0.6, player_radius * 0.5),
    ]
    rotated_points = [
        pygame.Vector2(p).rotate(angle) + player_pos for p in arrow_points
    ]
    pygame.draw.polygon(screen, "red", rotated_points)

    for projectile in projectiles:
        end_pos = projectile["pos"] + projectile["vel"].normalize() * 15
        pygame.draw.line(screen, "yellow", projectile["pos"], end_pos, 3)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    dt = clock.tick(60) / 1000

pygame.quit()