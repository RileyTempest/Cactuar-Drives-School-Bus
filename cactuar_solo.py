import pygame
import math
import sys
import random

# Initialize engine core
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PROTOCOL: CACTUAR_SHOE_PROTOCOL")
clock = pygame.time.Clock()

# Color Registers
COLOR_BG = (24, 20, 28)
COLOR_GRID = (45, 35, 50)
COLOR_CACTUS = (40, 190, 80)
COLOR_CACTUS_SHADOW = (20, 100, 45)
COLOR_FACE = (15, 15, 15)
COLOR_SHOE = (230, 60, 90)
COLOR_SHOE_SOLE = (250, 240, 230)
COLOR_SHOE_LACE = (255, 255, 255)

# --- PROCEDURAL HOT-SWAP SPRITE GENERATOR ---
def create_trunk_plane(w, h):
    """Static torso + face plane. Arms/legs are swapped in separately."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, COLOR_CACTUS, (w // 2 - 20, 40, 40, h - 140))
    pygame.draw.rect(surf, COLOR_CACTUS_SHADOW, (w // 2 - 20, 40, 6, h - 140))
    # Eyes and Mouth
    pygame.draw.rect(surf, COLOR_FACE, (w // 2 - 12, 60, 6, 12))
    pygame.draw.rect(surf, COLOR_FACE, (w // 2 + 6, 60, 6, 12))
    pygame.draw.rect(surf, COLOR_FACE, (w // 2 - 4, 85, 8, 14))
    # Hair Spikes
    pygame.draw.line(surf, COLOR_FACE, (w // 2 - 6, 40), (w // 2 - 10, 25), 2)
    pygame.draw.line(surf, COLOR_FACE, (w // 2, 40), (w // 2, 20), 2)
    pygame.draw.line(surf, COLOR_FACE, (w // 2 + 6, 40), (w // 2 + 12, 25), 2)
    return surf

def create_arm_plane(w, h, frame_type):
    """Bakes specific arm poses to hot-swap independently of legs."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2

    if frame_type == "ARMS_UP":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 20, 20, 20, 50))   # R arm raised
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, 20, 20, 50))   # L arm raised
    elif frame_type == "ARMS_OUT":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 20, 55, 45, 18))   # R arm out
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 65, 55, 45, 18))   # L arm out
    elif frame_type == "ARMS_WIGGLE_A":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 15, 30, 18, 45))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 20, 25, 35, 16))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 60, 65, 45, 16))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 33, 70, 16, 30))
    elif frame_type == "ARMS_WIGGLE_B":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 33, 30, 18, 45))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 65, 25, 35, 16))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 15, 65, 45, 16))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 17, 70, 16, 30))
    elif frame_type == "REACH_DOWN":
        # Both arms reaching down toward feet (for shoe-tying)
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 34, 40, 16, 70))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 18, 40, 16, 70))
    return surf

def create_leg_plane(w, h, frame_type):
    """Bakes specific leg poses to hot-swap independently of arms."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    base_y = h - 100

    if frame_type == "STANCE":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 22, base_y, 16, 60))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 6, base_y, 16, 60))
    elif frame_type == "KICK_A":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 30, base_y - 10, 16, 50))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, base_y + 30, 40, 14))  # kicked leg out
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 10, base_y + 5, 16, 55))
    elif frame_type == "KICK_B":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 26, base_y + 5, 16, 55))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 14, base_y - 10, 16, 50))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 14, base_y + 30, 40, 14))  # kicked leg out
    elif frame_type == "WIDE":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, base_y, 16, 60))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 24, base_y, 16, 60))
    elif frame_type == "SIT_BENT":
        # Knees bent, feet forward, for shoe-putting-on pose
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 24, base_y + 10, 16, 35))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 30, base_y + 40, 30, 16))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 8, base_y + 10, 16, 35))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 2, base_y + 40, 30, 16))
    return surf

# Pre-compile the surface database
FRAME_W, FRAME_H = 200, 250
TRUNK_FRONT = create_trunk_plane(FRAME_W, FRAME_H)
TRUNK_SIDE = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
pygame.draw.rect(TRUNK_SIDE, COLOR_CACTUS_SHADOW, (80, 40, 40, 70))

ARM_FRAMES = {
    "ARMS_UP": create_arm_plane(FRAME_W, FRAME_H, "ARMS_UP"),
    "ARMS_OUT": create_arm_plane(FRAME_W, FRAME_H, "ARMS_OUT"),
    "ARMS_WIGGLE_A": create_arm_plane(FRAME_W, FRAME_H, "ARMS_WIGGLE_A"),
    "ARMS_WIGGLE_B": create_arm_plane(FRAME_W, FRAME_H, "ARMS_WIGGLE_B"),
    "REACH_DOWN": create_arm_plane(FRAME_W, FRAME_H, "REACH_DOWN"),
}

LEG_FRAMES = {
    "STANCE": create_leg_plane(FRAME_W, FRAME_H, "STANCE"),
    "KICK_A": create_leg_plane(FRAME_W, FRAME_H, "KICK_A"),
    "KICK_B": create_leg_plane(FRAME_W, FRAME_H, "KICK_B"),
    "WIDE": create_leg_plane(FRAME_W, FRAME_H, "WIDE"),
    "SIT_BENT": create_leg_plane(FRAME_W, FRAME_H, "SIT_BENT"),
}

def draw_shoe(surf, x, y, on_foot, wiggle=0):
    """Draws a single goofy sneaker. If not on_foot, it sits on the ground waiting."""
    sx = x + wiggle
    sy = y
    pygame.draw.ellipse(surf, COLOR_SHOE_SOLE, (sx - 22, sy + 10, 44, 12))
    pygame.draw.rect(surf, COLOR_SHOE, (sx - 20, sy - 10, 40, 22), border_radius=8)
    pygame.draw.line(surf, COLOR_SHOE_LACE, (sx - 8, sy - 6), (sx + 8, sy + 2), 2)
    pygame.draw.line(surf, COLOR_SHOE_LACE, (sx + 8, sy - 6), (sx - 8, sy + 2), 2)

# Architecture Coordinates
cactuar_x, cactuar_y = 400, 380
shoe_l_ground = (cactuar_x - 90, cactuar_y + 175)
shoe_r_ground = (cactuar_x + 90, cactuar_y + 175)

# Simulation state counters
state = "GOOFY_DANCE"  # Options: GOOFY_DANCE -> SIT_DOWN -> SHOE_ON -> STAND_PROUD -> GOOFY_DANCE
state_timer = 0
angle = 0.0
pitch = 0.55
shoes_on = 0  # 0, 1, or 2 shoes equipped

running = True
while running:
    clock.tick(60)
    screen.fill(COLOR_BG)
    state_timer += 1

    for i in range(0, WIDTH, 40):
        pygame.draw.line(screen, COLOR_GRID, (i, 0), (i, HEIGHT))
    for i in range(0, HEIGHT, 40):
        pygame.draw.line(screen, COLOR_GRID, (0, i), (WIDTH, i))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    t_ms = pygame.time.get_ticks()
    beat = t_ms * 0.008

    # --- State controller machine ---
    if state == "GOOFY_DANCE" and state_timer > 260:
        state = "SIT_DOWN"
        state_timer = 0
    elif state == "SIT_DOWN" and state_timer > 60:
        state = "SHOE_ON_L"
        state_timer = 0
    elif state == "SHOE_ON_L" and state_timer > 120:
        shoes_on = 1
        state = "SHOE_ON_R"
        state_timer = 0
    elif state == "SHOE_ON_R" and state_timer > 120:
        shoes_on = 2
        state = "STAND_PROUD"
        state_timer = 0
    elif state == "STAND_PROUD" and state_timer > 90:
        state = "GOOFY_DANCE"
        state_timer = 0
        shoes_on = 0  # reset the bit for looping demo

    shake_x, shake_y = 0, 0
    bob_y = 0

    if state == "GOOFY_DANCE":
        # Big goofy full-body sway, arms and legs hot-swap on DIFFERENT beat divisors
        # so they never sync up -- that's the goofiness.
        angle = math.sin(beat * 0.6) * 0.9
        bob_y = int(math.sin(beat * 2.0) * 14)
        arm_key = "ARMS_WIGGLE_A" if (int(beat * 1.3) % 2 == 0) else "ARMS_WIGGLE_B"
        leg_key = "KICK_A" if (int(beat * 0.7) % 2 == 0) else "KICK_B"

    elif state == "SIT_DOWN":
        # Settle from dance into a bent-knee sit pose
        settle = min(state_timer / 60.0, 1.0)
        angle *= (1.0 - settle)
        bob_y = int(20 * settle)
        arm_key = "REACH_DOWN"
        leg_key = "SIT_BENT"

    elif state == "SHOE_ON_L":
        angle = 0.0
        bob_y = 20
        arm_key = "REACH_DOWN"
        leg_key = "SIT_BENT"
        shake_x = int(math.sin(t_ms * 0.03) * 2)  # tugging-the-shoe-on wobble

    elif state == "SHOE_ON_R":
        angle = 0.0
        bob_y = 20
        arm_key = "REACH_DOWN"
        leg_key = "SIT_BENT"
        shake_x = int(math.sin(t_ms * 0.03) * 2)

    elif state == "STAND_PROUD":
        angle = 0.0
        rise = min(state_timer / 40.0, 1.0)
        bob_y = int(20 * (1.0 - rise))
        arm_key = "ARMS_UP"
        leg_key = "WIDE"

    # --- Compose composite frame ---
    active_front = TRUNK_FRONT.copy()
    active_front.blit(LEG_FRAMES[leg_key], (0, 0))
    active_front.blit(ARM_FRAMES[arm_key], (0, 0))

    # --- Affine perspective projection ---
    f_cos = math.cos(angle)
    s_cos = math.cos(angle + math.pi / 2)

    f_scale_x = max(int(abs(f_cos) * FRAME_W), 1)
    s_scale_x = max(int(abs(s_cos) * FRAME_W), 1)
    scale_y = int(FRAME_H * math.cos(pitch))

    f_proj = pygame.transform.scale(active_front, (f_scale_x, scale_y))
    s_proj = pygame.transform.scale(TRUNK_SIDE, (s_scale_x, scale_y))

    rx = cactuar_x + shake_x
    ry = cactuar_y + shake_y + bob_y

    # Depth-sorted cross-plane blit
    if f_cos >= 0:
        if s_cos >= 0:
            screen.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
            screen.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))
        else:
            screen.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))
            screen.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
    else:
        if s_cos >= 0:
            screen.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))
            screen.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
        else:
            screen.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
            screen.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))

    # --- Draw shoes: on the ground until equipped, then stuck to feet ---
    l_wiggle = int(math.sin(t_ms * 0.02) * 3) if state == "SHOE_ON_L" else 0
    r_wiggle = int(math.sin(t_ms * 0.02) * 3) if state == "SHOE_ON_R" else 0

    if shoes_on < 1:
        draw_shoe(screen, *shoe_l_ground, on_foot=False, wiggle=l_wiggle)
    if shoes_on < 2:
        draw_shoe(screen, *shoe_r_ground, on_foot=False, wiggle=r_wiggle)
    if shoes_on >= 1:
        draw_shoe(screen, rx - 55, ry + 165, on_foot=True)
    if shoes_on >= 2:
        draw_shoe(screen, rx + 55, ry + 165, on_foot=True)

    # UI Telemetry Readout
    font = pygame.font.SysFont(None, 24)
    status_lbl = font.render(f"EXEC SYSTEM: {state} // SHOES: {shoes_on}/2", True, (240, 80, 140))
    hint_lbl = font.render("ARMS + LEGS HOT-SWAPPED ON INDEPENDENT BEAT DIVISORS", True, (150, 220, 255))
    screen.blit(status_lbl, (20, 20))
    screen.blit(hint_lbl, (20, 48))

    pygame.display.flip()

pygame.quit()
sys.exit()
