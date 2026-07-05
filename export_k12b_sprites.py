"""
K-12B BLUEPRINT -> HOT-SWAP SPRITE PLANES
Deconstructs the green mech turnaround sheet into the same trunk/arm/leg
plane structure used by the cactuar rig, but shaped to match the blueprint:
- forward-swept angular shoulder pauldrons
- compact head sunk low between the shoulders
- boxy chest with central hatch/vent detail
- wide hip skirt
- thick digitigrade thighs
- lower legs with a heel-thruster bulge
- blocky angled feet

Exports every plane to individual transparent PNGs.
Standalone -- not wired into the main game scripts.
"""
import pygame
import os

pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

OUT_DIR = "/mnt/user-data/outputs/k12b_sprites"
os.makedirs(OUT_DIR, exist_ok=True)

FRAME_W, FRAME_H = 260, 320

# Color registers pulled from the blueprint's flat cel-shaded palette
COLOR_HULL       = (110, 170, 90)    # main olive-green plating
COLOR_HULL_DARK  = (70, 120, 60)     # shadow-side plating
COLOR_HULL_LIGHT = (150, 200, 130)   # highlight edge
COLOR_JOINT      = (55, 60, 65)      # dark joint/socket housing
COLOR_VENT       = (35, 40, 45)      # chest hatch / vents
COLOR_VISOR      = (40, 45, 50)      # head visor slit
COLOR_ACCENT     = (150, 190, 60)    # the yellow-green accent chevrons on the sheet

def poly(surf, color, points):
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, (20, 25, 20), points, 1)

# ------------------------------------------------------------------
# TRUNK: head + chest + hip skirt (static core, arms/legs swap on top)
# ------------------------------------------------------------------
def create_trunk_plane(w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    # Hip skirt / pelvis block (wide, trapezoidal, sits low)
    poly(surf, COLOR_HULL_DARK, [
        (cx - 46, 150), (cx + 46, 150), (cx + 54, 195), (cx - 54, 195)
    ])
    poly(surf, COLOR_HULL, [
        (cx - 40, 150), (cx + 40, 150), (cx + 46, 188), (cx - 46, 188)
    ])

    # Chest / torso core (boxy, slightly tapered waist)
    poly(surf, COLOR_HULL, [
        (cx - 44, 70), (cx + 44, 70), (cx + 50, 155), (cx - 50, 155)
    ])
    poly(surf, COLOR_HULL_DARK, [
        (cx - 44, 70), (cx - 30, 70), (cx - 36, 155), (cx - 50, 155)
    ])
    poly(surf, COLOR_HULL_LIGHT, [
        (cx + 30, 70), (cx + 44, 70), (cx + 50, 155), (cx + 36, 155)
    ])

    # Central chest hatch / vent detail (matches the small square on the sheet)
    poly(surf, COLOR_VENT, [
        (cx - 12, 95), (cx + 12, 95), (cx + 12, 118), (cx - 12, 118)
    ])
    pygame.draw.rect(surf, COLOR_HULL_LIGHT, (cx - 8, 99, 16, 4))

    # Collar / neck housing (recessed block where head sits)
    poly(surf, COLOR_HULL_DARK, [
        (cx - 26, 55), (cx + 26, 55), (cx + 22, 72), (cx - 22, 72)
    ])

    # Head (compact, sunk low, small visor slit)
    poly(surf, COLOR_HULL, [
        (cx - 20, 30), (cx + 20, 30), (cx + 22, 58), (cx - 22, 58)
    ])
    poly(surf, COLOR_HULL_LIGHT, [
        (cx - 20, 30), (cx + 20, 30), (cx + 18, 38), (cx - 18, 38)
    ])
    pygame.draw.rect(surf, COLOR_VISOR, (cx - 14, 40, 28, 6))

    return surf

def create_trunk_side_plane(w, h):
    """Profile silhouette used for the perspective cross-plane, matching
    the side-view forward lean visible on the blueprint's left figure."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    poly(surf, COLOR_HULL_DARK, [
        (cx - 30, 70), (cx + 40, 78), (cx + 46, 155), (cx - 34, 150)
    ])
    poly(surf, COLOR_HULL_DARK, [
        (cx - 34, 150), (cx + 46, 155), (cx + 50, 190), (cx - 40, 188)
    ])
    poly(surf, COLOR_JOINT, [
        (cx - 18, 34), (cx + 24, 40), (cx + 20, 58), (cx - 18, 55)
    ])
    return surf

# ------------------------------------------------------------------
# ARMS: shoulder pauldron (forward-swept, angular) + forearm poses
# ------------------------------------------------------------------
def _pauldron(surf, side_sign, cx, lift=0):
    """side_sign: -1 = left shoulder, +1 = right shoulder.
    Forward-swept angular block matching the blueprint's pauldrons."""
    sx = cx + side_sign * 58
    top_sweep = side_sign * 22
    pts = [
        (sx - 26 * side_sign, 40 - lift),
        (sx + 30 * side_sign + top_sweep, 26 - lift),
        (sx + 40 * side_sign + top_sweep, 52 - lift),
        (sx + 18 * side_sign, 90 - lift),
        (sx - 22 * side_sign, 92 - lift),
    ]
    poly(surf, COLOR_HULL, pts)
    # highlight sliver along the leading edge
    hl = [
        (sx - 10 * side_sign, 42 - lift),
        (sx + 26 * side_sign + top_sweep, 30 - lift),
        (sx + 20 * side_sign, 50 - lift),
    ]
    poly(surf, COLOR_HULL_LIGHT, hl)

def _forearm(surf, side_sign, cx, angle_state):
    sx = cx + side_sign * 66
    if angle_state == "DOWN":
        poly(surf, COLOR_JOINT, [(sx - 14 * side_sign, 88), (sx + 16 * side_sign, 88),
                                  (sx + 16 * side_sign, 110), (sx - 14 * side_sign, 110)])
        poly(surf, COLOR_HULL_DARK, [(sx - 14 * side_sign, 108), (sx + 16 * side_sign, 108),
                                      (sx + 18 * side_sign, 165), (sx - 12 * side_sign, 165)])
    elif angle_state == "RAISED":
        poly(surf, COLOR_JOINT, [(sx - 14 * side_sign, 60), (sx + 16 * side_sign, 60),
                                  (sx + 16 * side_sign, 82), (sx - 14 * side_sign, 82)])
        poly(surf, COLOR_HULL_DARK, [(sx - 30 * side_sign, 20), (sx + 4 * side_sign, 30),
                                      (sx + 8 * side_sign, 78), (sx - 26 * side_sign, 68)])
    elif angle_state == "FORWARD":
        poly(surf, COLOR_JOINT, [(sx - 14 * side_sign, 90), (sx + 16 * side_sign, 90),
                                  (sx + 16 * side_sign, 112), (sx - 14 * side_sign, 112)])
        poly(surf, COLOR_HULL_DARK, [(sx - 10 * side_sign, 110), (sx + 40 * side_sign, 100),
                                      (sx + 44 * side_sign, 122), (sx - 6 * side_sign, 132)])

def create_arm_plane(w, h, frame_type):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    if frame_type == "ARMS_NEUTRAL":
        _pauldron(surf, -1, cx)
        _pauldron(surf, 1, cx)
        _forearm(surf, -1, cx, "DOWN")
        _forearm(surf, 1, cx, "DOWN")
    elif frame_type == "ARMS_RAISED":
        _pauldron(surf, -1, cx, lift=10)
        _pauldron(surf, 1, cx, lift=10)
        _forearm(surf, -1, cx, "RAISED")
        _forearm(surf, 1, cx, "RAISED")
    elif frame_type == "ARMS_WIGGLE_A":
        _pauldron(surf, -1, cx, lift=6)
        _pauldron(surf, 1, cx)
        _forearm(surf, -1, cx, "RAISED")
        _forearm(surf, 1, cx, "FORWARD")
    elif frame_type == "ARMS_WIGGLE_B":
        _pauldron(surf, -1, cx)
        _pauldron(surf, 1, cx, lift=6)
        _forearm(surf, -1, cx, "FORWARD")
        _forearm(surf, 1, cx, "RAISED")
    elif frame_type == "ARMS_FORWARD":
        _pauldron(surf, -1, cx)
        _pauldron(surf, 1, cx)
        _forearm(surf, -1, cx, "FORWARD")
        _forearm(surf, 1, cx, "FORWARD")

    return surf

# ------------------------------------------------------------------
# LEGS: thick digitigrade thigh + heel-thruster shin + angled foot
# ------------------------------------------------------------------
def _leg(surf, side_sign, cx, base_y, lift_height=0, forward_offset=0):
    sx = cx + side_sign * 24 + forward_offset
    fy = base_y - lift_height

    # Thigh (thick, tapered)
    poly(surf, COLOR_HULL_DARK if side_sign < 0 else COLOR_HULL, [
        (sx - 20, fy), (sx + 20, fy), (sx + 16, fy + 55), (sx - 16, fy + 55)
    ])
    # Knee joint block
    poly(surf, COLOR_JOINT, [
        (sx - 16, fy + 52), (sx + 16, fy + 52), (sx + 16, fy + 66), (sx - 16, fy + 66)
    ])
    # Shin with heel-thruster bulge (the round housing on the blueprint's ankle)
    poly(surf, COLOR_HULL_DARK if side_sign < 0 else COLOR_HULL, [
        (sx - 14, fy + 64), (sx + 14, fy + 64), (sx + 18, fy + 108), (sx - 18, fy + 108)
    ])
    pygame.draw.circle(surf, COLOR_JOINT, (sx + side_sign * 10, fy + 100), 12)
    pygame.draw.circle(surf, COLOR_HULL_LIGHT, (sx + side_sign * 10, fy + 100), 12, 2)

    # Angled blocky foot
    poly(surf, COLOR_HULL, [
        (sx - 20, fy + 106), (sx + 22, fy + 106), (sx + 26, fy + 122),
        (sx + 6, fy + 128), (sx - 24, fy + 122)
    ])
    poly(surf, COLOR_HULL_DARK, [
        (sx - 20, fy + 106), (sx - 6, fy + 106), (sx - 2, fy + 122), (sx - 24, fy + 122)
    ])

def create_leg_plane(w, h, frame_type):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    base_y = h - 140

    if frame_type == "STANCE":
        _leg(surf, -1, cx, base_y)
        _leg(surf, 1, cx, base_y)
    elif frame_type == "KICK_A":  # left leg lifted / stepping forward
        _leg(surf, 1, cx, base_y)
        _leg(surf, -1, cx, base_y, lift_height=28, forward_offset=-18)
    elif frame_type == "KICK_B":  # right leg lifted / stepping forward
        _leg(surf, -1, cx, base_y)
        _leg(surf, 1, cx, base_y, lift_height=28, forward_offset=18)
    elif frame_type == "WIDE":
        _leg(surf, -1, cx - 14, base_y)
        _leg(surf, 1, cx + 14, base_y)

    return surf

# ------------------------------------------------------------------
# Accent chevrons (the yellow-green corner markers from the sheet) --
# purely decorative overlay plane, handy to keep separate in Photoshop
# ------------------------------------------------------------------
def create_accent_plane(w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    poly(surf, COLOR_ACCENT, [(20, 20), (70, 20), (50, 40), (20, 45)])
    poly(surf, COLOR_ACCENT, [(w - 70, 20), (w - 20, 20), (w - 20, 45), (w - 50, 40)])
    poly(surf, COLOR_ACCENT, [(20, h - 45), (45, h - 45), (45, h - 20), (20, h - 20)])
    poly(surf, COLOR_ACCENT, [(w - 45, h - 45), (w - 20, h - 45), (w - 20, h - 20), (w - 45, h - 20)])
    return surf

# --- Build every sprite plane ---
sprites = {}
sprites["trunk_front"] = create_trunk_plane(FRAME_W, FRAME_H)
sprites["trunk_side"] = create_trunk_side_plane(FRAME_W, FRAME_H)
sprites["accent_chevrons"] = create_accent_plane(FRAME_W, FRAME_H)

for arm_key in ["ARMS_NEUTRAL", "ARMS_RAISED", "ARMS_WIGGLE_A", "ARMS_WIGGLE_B", "ARMS_FORWARD"]:
    sprites[f"arm_{arm_key.lower()}"] = create_arm_plane(FRAME_W, FRAME_H, arm_key)

for leg_key in ["STANCE", "KICK_A", "KICK_B", "WIDE"]:
    sprites[f"leg_{leg_key.lower()}"] = create_leg_plane(FRAME_W, FRAME_H, leg_key)

# --- Composited full-body reference frames ---
composites = {
    "composite_idle_stance": ("ARMS_NEUTRAL", "STANCE"),
    "composite_walk_kick_a": ("ARMS_WIGGLE_A", "KICK_A"),
    "composite_walk_kick_b": ("ARMS_WIGGLE_B", "KICK_B"),
    "composite_wide_raised": ("ARMS_RAISED", "WIDE"),
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
