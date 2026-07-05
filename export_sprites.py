"""
Exports every cactuar sprite plane (trunk, arms, legs, and the side/shadow
plane) to individual transparent PNGs for use in Photoshop.

Pulled directly from cactuar_mech.py's sprite generator functions --
same geometry, same colors, no game loop needed.
"""
import pygame
import os

pygame.init()
# Dummy display surface required for convert_alpha/Surface ops on some setups
pygame.display.set_mode((1, 1), pygame.HIDDEN)

OUT_DIR = "/mnt/user-data/outputs/cactuar_sprites"
os.makedirs(OUT_DIR, exist_ok=True)

COLOR_CACTUS = (40, 190, 80)
COLOR_CACTUS_SHADOW = (20, 100, 45)
COLOR_FACE = (15, 15, 15)

FRAME_W, FRAME_H = 200, 250

def create_trunk_plane(w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, COLOR_CACTUS, (w // 2 - 20, 40, 40, h - 140))
    pygame.draw.rect(surf, COLOR_CACTUS_SHADOW, (w // 2 - 20, 40, 6, h - 140))
    pygame.draw.rect(surf, COLOR_FACE, (w // 2 - 12, 60, 6, 12))
    pygame.draw.rect(surf, COLOR_FACE, (w // 2 + 6, 60, 6, 12))
    pygame.draw.rect(surf, COLOR_FACE, (w // 2 - 4, 85, 8, 14))
    pygame.draw.line(surf, COLOR_FACE, (w // 2 - 6, 40), (w // 2 - 10, 25), 2)
    pygame.draw.line(surf, COLOR_FACE, (w // 2, 40), (w // 2, 20), 2)
    pygame.draw.line(surf, COLOR_FACE, (w // 2 + 6, 40), (w // 2 + 12, 25), 2)
    return surf

def create_arm_plane(w, h, frame_type):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2

    if frame_type == "ARMS_UP":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 20, 20, 20, 50))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, 20, 20, 50))
    elif frame_type == "ARMS_OUT":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 20, 55, 45, 18))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 65, 55, 45, 18))
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
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 34, 40, 16, 70))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 18, 40, 16, 70))
    return surf

def create_leg_plane(w, h, frame_type):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    base_y = h - 100

    if frame_type == "STANCE":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 22, base_y, 16, 60))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 6, base_y, 16, 60))
    elif frame_type == "KICK_A":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 30, base_y - 10, 16, 50))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, base_y + 30, 40, 14))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 10, base_y + 5, 16, 55))
    elif frame_type == "KICK_B":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 26, base_y + 5, 16, 55))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 14, base_y - 10, 16, 50))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 14, base_y + 30, 40, 14))
    elif frame_type == "WIDE":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, base_y, 16, 60))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 24, base_y, 16, 60))
    elif frame_type == "SIT_BENT":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 24, base_y + 10, 16, 35))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 30, base_y + 40, 30, 16))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 8, base_y + 10, 16, 35))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 2, base_y + 40, 30, 16))
    return surf

# --- Build every sprite plane ---
sprites = {}

sprites["trunk_front"] = create_trunk_plane(FRAME_W, FRAME_H)

trunk_side = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
pygame.draw.rect(trunk_side, COLOR_CACTUS_SHADOW, (80, 40, 40, 70))
sprites["trunk_side"] = trunk_side

for arm_key in ["ARMS_UP", "ARMS_OUT", "ARMS_WIGGLE_A", "ARMS_WIGGLE_B", "REACH_DOWN"]:
    sprites[f"arm_{arm_key.lower()}"] = create_arm_plane(FRAME_W, FRAME_H, arm_key)

for leg_key in ["STANCE", "KICK_A", "KICK_B", "WIDE", "SIT_BENT"]:
    sprites[f"leg_{leg_key.lower()}"] = create_leg_plane(FRAME_W, FRAME_H, leg_key)

# --- Bonus: composited full-body reference frames (trunk + arm + leg) ---
composites = {
    "composite_idle_stance":     ("ARMS_OUT", "STANCE"),
    "composite_walk_kick_a":     ("ARMS_WIGGLE_A", "KICK_A"),
    "composite_walk_kick_b":     ("ARMS_WIGGLE_B", "KICK_B"),
    "composite_wide_armsup":     ("ARMS_UP", "WIDE"),
    "composite_shoe_on_sitting": ("REACH_DOWN", "SIT_BENT"),
}
for name, (arm_key, leg_key) in composites.items():
    frame = sprites["trunk_front"].copy()
    frame.blit(sprites[f"leg_{leg_key.lower()}"], (0, 0))
    frame.blit(sprites[f"arm_{arm_key.lower()}"], (0, 0))
    sprites[name] = frame

# --- Export ---
for name, surf in sprites.items():
    path = os.path.join(OUT_DIR, f"{name}.png")
    pygame.image.save(surf, path)
    print(f"saved {path}")

print(f"\nExported {len(sprites)} PNGs to {OUT_DIR}")
