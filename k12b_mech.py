import pygame
import sys
import math
import random
import numpy as np
from enum import Enum, auto

# --- 構成 (Initialization & Constants) ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Protocol VIPER: K-12B Symbiotic Evasion Vectors")
clock = pygame.time.Clock()

MAP_W, MAP_H = 15, 100
TILE_W, TILE_H = 64, 32

class StrafeCause(Enum):
    MANUAL = auto()
    RECOIL_OVERFLOW = auto()

# UI: Massive Lateral Vectors (75% larger, mid-screen anchors)
BTN_STRAFE_L = pygame.Rect(20, (HEIGHT // 2) - 50, 300, 98)
BTN_STRAFE_R = pygame.Rect(WIDTH - 320, (HEIGHT // 2) - 50, 300, 98)

# UI: Throttle & Trauma (Repositioned to avoid the new strafe zones)
BTN_REV = pygame.Rect(WIDTH - 220, HEIGHT - 128, 200, 56)
BTN_THR = pygame.Rect(WIDTH - 220, HEIGHT - 64, 200, 56)

BTN_SHOCK_L_SHOULDER = pygame.Rect(20, HEIGHT - 192, 260, 56)
BTN_SLIP_R_FOOT = pygame.Rect(20, HEIGHT - 128, 260, 56)
BTN_CORE_IMPACT = pygame.Rect(20, HEIGHT - 64, 260, 56)

# --- 動的グラフ (Dynamic Graph: Slime & Path) ---
def creep_slime(slime_matrix):
    padded = np.pad(slime_matrix, 1, mode='edge')
    neighbor_max = np.maximum.reduce([
        padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:]
    ])
    return np.clip(slime_matrix * 0.985 + (neighbor_max - 0.05) * 0.05, 0.0, 1.0)

class AutoCarver:
    def __init__(self, start_x, start_y):
        self.gx = start_x
        self.gy = start_y
        self.timer = 0.0
        self.step_interval = 0.3

    def update(self, dt, slime_matrix, golden_path_matrix):
        self.timer += dt
        if self.timer >= self.step_interval:
            self.timer = 0.0

            best_cell = (self.gx, self.gy)
            best_w = float('inf')
            for dx, dy in [(-1, 1), (0, 1), (1, 1), (0, 2)]:
                nx, ny = self.gx + dx, self.gy + dy
                if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                    if slime_matrix[nx, ny] < best_w:
                        best_cell = (nx, ny)
                        best_w = slime_matrix[nx, ny]

            self.gx, self.gy = best_cell

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = self.gx + dx, self.gy + dy
                    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                        falloff = 1.0 if (dx == 0 and dy == 0) else 0.4
                        golden_path_matrix[nx, ny] = min(1.0, golden_path_matrix[nx, ny] + falloff)

# --- 幾何学 (Geometry & Projection Math) ---
def project_iso(x, y, z):
    iso_x = (x - y) * (TILE_W / 2.0)
    iso_y = ((x + y) * (TILE_H / 2.0)) - (z * TILE_H)
    return iso_x, iso_y

def rotate_z(x, y, z, angle_degrees):
    rad = math.radians(angle_degrees)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    rx = x * cos_a - y * sin_a
    ry = x * sin_a + y * cos_a
    return rx, ry, z

class StaticBlock:
    def __init__(self, gx, gy, gz, btype):
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.btype = btype
        self.is_entity = False
        self.highlight = None
        self.path_weight = 0.0

        if self.btype == 'grass':
            self.base_colors = ((50, 55, 60), (30, 35, 40), (15, 20, 25))
        elif self.btype == 'chasm':
            self.base_colors = ((20, 15, 25), (10, 5, 15), (0, 0, 0))

    def draw(self, surface, cx, cy):
        iso_x, iso_y = project_iso(self.gx, self.gy, self.gz)
        ox, oy = cx + iso_x, cy + iso_y

        top = [(ox, oy - TILE_H), (ox + TILE_W//2, oy - TILE_H//2), (ox, oy), (ox - TILE_W//2, oy - TILE_H//2)]
        left = [(ox - TILE_W//2, oy - TILE_H//2), (ox, oy), (ox, oy + TILE_H), (ox - TILE_W//2, oy + TILE_H//2)]
        right = [(ox, oy), (ox + TILE_W//2, oy - TILE_H//2), (ox + TILE_W//2, oy + TILE_H//2), (ox, oy + TILE_H)]

        top_color = list(self.base_colors[0])
        if self.path_weight > 0.05 and self.btype != 'chasm':
            top_color[0] = min(255, int(top_color[0] + (0 * self.path_weight)))
            top_color[1] = min(255, int(top_color[1] + (180 * self.path_weight)))
            top_color[2] = min(255, int(top_color[2] + (200 * self.path_weight)))

        top_color = tuple(top_color)

        if self.highlight == 'yellow':
            top_color = (255, 220, 50)
        elif self.highlight == 'purple':
            top_color = (180, 50, 220)
        elif self.highlight == 'purple_lifted':
            # Brighter purple flash: this foot's lane AND the foot is currently airborne
            top_color = (230, 120, 255)

        pygame.draw.polygon(surface, top_color, top)
        if self.btype != 'chasm':
            pygame.draw.polygon(surface, self.base_colors[1], left)
            pygame.draw.polygon(surface, self.base_colors[2], right)
        for poly in [top, left, right]:
            pygame.draw.polygon(surface, (0, 0, 0), poly, 1)

# ============================================================
# K-12B SPRITE PLANES (deconstructed from the blueprint turnaround sheet)
# ============================================================
COLOR_HULL       = (110, 170, 90)    # main olive-green plating
COLOR_HULL_DARK  = (70, 120, 60)     # shadow-side plating
COLOR_HULL_LIGHT = (150, 200, 130)   # highlight edge
COLOR_JOINT      = (55, 60, 65)      # dark joint/socket housing
COLOR_VENT       = (35, 40, 45)      # chest hatch / vents
COLOR_VISOR      = (40, 45, 50)      # head visor slit

def _poly(surf, color, points):
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, (20, 25, 20), points, 1)

def create_trunk_plane(w, h):
    """Boxy chest + collar + sunk head + wide hip skirt. Static core;
    arms/legs are swapped in separately."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    # Hip skirt / pelvis block
    _poly(surf, COLOR_HULL_DARK, [
        (cx - 46, 150), (cx + 46, 150), (cx + 54, 195), (cx - 54, 195)
    ])
    _poly(surf, COLOR_HULL, [
        (cx - 40, 150), (cx + 40, 150), (cx + 46, 188), (cx - 46, 188)
    ])

    # Chest / torso core
    _poly(surf, COLOR_HULL, [
        (cx - 44, 70), (cx + 44, 70), (cx + 50, 155), (cx - 50, 155)
    ])
    _poly(surf, COLOR_HULL_DARK, [
        (cx - 44, 70), (cx - 30, 70), (cx - 36, 155), (cx - 50, 155)
    ])
    _poly(surf, COLOR_HULL_LIGHT, [
        (cx + 30, 70), (cx + 44, 70), (cx + 50, 155), (cx + 36, 155)
    ])

    # Central chest hatch / vent
    _poly(surf, COLOR_VENT, [
        (cx - 12, 95), (cx + 12, 95), (cx + 12, 118), (cx - 12, 118)
    ])
    pygame.draw.rect(surf, COLOR_HULL_LIGHT, (cx - 8, 99, 16, 4))

    # Collar / neck housing
    _poly(surf, COLOR_HULL_DARK, [
        (cx - 26, 55), (cx + 26, 55), (cx + 22, 72), (cx - 22, 72)
    ])

    # Head (compact, sunk low, visor slit)
    _poly(surf, COLOR_HULL, [
        (cx - 20, 30), (cx + 20, 30), (cx + 22, 58), (cx - 22, 58)
    ])
    _poly(surf, COLOR_HULL_LIGHT, [
        (cx - 20, 30), (cx + 20, 30), (cx + 18, 38), (cx - 18, 38)
    ])
    pygame.draw.rect(surf, COLOR_VISOR, (cx - 14, 40, 28, 6))

    return surf

def create_trunk_side_plane(w, h):
    """Profile silhouette for the perspective cross-plane."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    _poly(surf, COLOR_HULL_DARK, [
        (cx - 30, 70), (cx + 40, 78), (cx + 46, 155), (cx - 34, 150)
    ])
    _poly(surf, COLOR_HULL_DARK, [
        (cx - 34, 150), (cx + 46, 155), (cx + 50, 190), (cx - 40, 188)
    ])
    _poly(surf, COLOR_JOINT, [
        (cx - 18, 34), (cx + 24, 40), (cx + 20, 58), (cx - 18, 55)
    ])
    return surf

def _pauldron(surf, side_sign, cx, lift=0):
    """side_sign: -1 = left shoulder, +1 = right shoulder. Forward-swept
    angular block matching the blueprint's pauldrons."""
    sx = cx + side_sign * 58
    top_sweep = side_sign * 22
    pts = [
        (sx - 26 * side_sign, 40 - lift),
        (sx + 30 * side_sign + top_sweep, 26 - lift),
        (sx + 40 * side_sign + top_sweep, 52 - lift),
        (sx + 18 * side_sign, 90 - lift),
        (sx - 22 * side_sign, 92 - lift),
    ]
    _poly(surf, COLOR_HULL, pts)
    hl = [
        (sx - 10 * side_sign, 42 - lift),
        (sx + 26 * side_sign + top_sweep, 30 - lift),
        (sx + 20 * side_sign, 50 - lift),
    ]
    _poly(surf, COLOR_HULL_LIGHT, hl)

def _forearm(surf, side_sign, cx, angle_state):
    sx = cx + side_sign * 66
    if angle_state == "DOWN":
        _poly(surf, COLOR_JOINT, [(sx - 14 * side_sign, 88), (sx + 16 * side_sign, 88),
                                   (sx + 16 * side_sign, 110), (sx - 14 * side_sign, 110)])
        _poly(surf, COLOR_HULL_DARK, [(sx - 14 * side_sign, 108), (sx + 16 * side_sign, 108),
                                       (sx + 18 * side_sign, 165), (sx - 12 * side_sign, 165)])
    elif angle_state == "RAISED":
        _poly(surf, COLOR_JOINT, [(sx - 14 * side_sign, 60), (sx + 16 * side_sign, 60),
                                   (sx + 16 * side_sign, 82), (sx - 14 * side_sign, 82)])
        _poly(surf, COLOR_HULL_DARK, [(sx - 30 * side_sign, 20), (sx + 4 * side_sign, 30),
                                       (sx + 8 * side_sign, 78), (sx - 26 * side_sign, 68)])
    elif angle_state == "FORWARD":
        _poly(surf, COLOR_JOINT, [(sx - 14 * side_sign, 90), (sx + 16 * side_sign, 90),
                                   (sx + 16 * side_sign, 112), (sx - 14 * side_sign, 112)])
        _poly(surf, COLOR_HULL_DARK, [(sx - 10 * side_sign, 110), (sx + 40 * side_sign, 100),
                                       (sx + 44 * side_sign, 122), (sx - 6 * side_sign, 132)])

def create_arm_plane(w, h, frame_type):
    """Bakes specific arm poses (pauldron + forearm) to hot-swap
    independently of legs."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    if frame_type == "ARMS_NEUTRAL":
        _pauldron(surf, -1, cx); _pauldron(surf, 1, cx)
        _forearm(surf, -1, cx, "DOWN"); _forearm(surf, 1, cx, "DOWN")
    elif frame_type == "ARMS_RAISED":
        _pauldron(surf, -1, cx, lift=10); _pauldron(surf, 1, cx, lift=10)
        _forearm(surf, -1, cx, "RAISED"); _forearm(surf, 1, cx, "RAISED")
    elif frame_type == "ARMS_WIGGLE_A":
        _pauldron(surf, -1, cx, lift=6); _pauldron(surf, 1, cx)
        _forearm(surf, -1, cx, "RAISED"); _forearm(surf, 1, cx, "FORWARD")
    elif frame_type == "ARMS_WIGGLE_B":
        _pauldron(surf, -1, cx); _pauldron(surf, 1, cx, lift=6)
        _forearm(surf, -1, cx, "FORWARD"); _forearm(surf, 1, cx, "RAISED")
    elif frame_type == "ARMS_FORWARD":
        _pauldron(surf, -1, cx); _pauldron(surf, 1, cx)
        _forearm(surf, -1, cx, "FORWARD"); _forearm(surf, 1, cx, "FORWARD")
    return surf

def _leg(surf, side_sign, cx, base_y, lift_height=0, forward_offset=0):
    """side_sign: -1 = left leg, +1 = right leg. Thick digitigrade thigh,
    knee joint, heel-thruster bulge shin, angled blocky foot."""
    sx = cx + side_sign * 24 + forward_offset
    fy = base_y - lift_height
    shade = COLOR_HULL_DARK if side_sign < 0 else COLOR_HULL

    _poly(surf, shade, [
        (sx - 20, fy), (sx + 20, fy), (sx + 16, fy + 55), (sx - 16, fy + 55)
    ])
    _poly(surf, COLOR_JOINT, [
        (sx - 16, fy + 52), (sx + 16, fy + 52), (sx + 16, fy + 66), (sx - 16, fy + 66)
    ])
    _poly(surf, shade, [
        (sx - 14, fy + 64), (sx + 14, fy + 64), (sx + 18, fy + 108), (sx - 18, fy + 108)
    ])
    pygame.draw.circle(surf, COLOR_JOINT, (sx + side_sign * 10, fy + 100), 12)
    pygame.draw.circle(surf, COLOR_HULL_LIGHT, (sx + side_sign * 10, fy + 100), 12, 2)

    _poly(surf, COLOR_HULL, [
        (sx - 20, fy + 106), (sx + 22, fy + 106), (sx + 26, fy + 122),
        (sx + 6, fy + 128), (sx - 24, fy + 122)
    ])
    _poly(surf, COLOR_HULL_DARK, [
        (sx - 20, fy + 106), (sx - 6, fy + 106), (sx - 2, fy + 122), (sx - 24, fy + 122)
    ])

def create_leg_plane(w, h, frame_type):
    """STANCE = both feet grounded. KICK_A = LEFT foot lifted.
    KICK_B = RIGHT foot lifted. WIDE = idle braced stance."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    base_y = h - 140

    if frame_type == "STANCE":
        _leg(surf, -1, cx, base_y); _leg(surf, 1, cx, base_y)
    elif frame_type == "KICK_A":
        _leg(surf, 1, cx, base_y)
        _leg(surf, -1, cx, base_y, lift_height=28, forward_offset=-18)
    elif frame_type == "KICK_B":
        _leg(surf, -1, cx, base_y)
        _leg(surf, 1, cx, base_y, lift_height=28, forward_offset=18)
    elif frame_type == "WIDE":
        _leg(surf, -1, cx - 14, base_y); _leg(surf, 1, cx + 14, base_y)
    return surf

FRAME_W, FRAME_H = 260, 320
TRUNK_FRONT = create_trunk_plane(FRAME_W, FRAME_H)
TRUNK_SIDE = create_trunk_side_plane(FRAME_W, FRAME_H)

ARM_FRAMES = {
    "ARMS_NEUTRAL": create_arm_plane(FRAME_W, FRAME_H, "ARMS_NEUTRAL"),
    "ARMS_RAISED": create_arm_plane(FRAME_W, FRAME_H, "ARMS_RAISED"),
    "ARMS_WIGGLE_A": create_arm_plane(FRAME_W, FRAME_H, "ARMS_WIGGLE_A"),
    "ARMS_WIGGLE_B": create_arm_plane(FRAME_W, FRAME_H, "ARMS_WIGGLE_B"),
    "ARMS_FORWARD": create_arm_plane(FRAME_W, FRAME_H, "ARMS_FORWARD"),
}

LEG_FRAMES = {
    "STANCE": create_leg_plane(FRAME_W, FRAME_H, "STANCE"),
    "KICK_A": create_leg_plane(FRAME_W, FRAME_H, "KICK_A"),
    "KICK_B": create_leg_plane(FRAME_W, FRAME_H, "KICK_B"),
    "WIDE": create_leg_plane(FRAME_W, FRAME_H, "WIDE"),
}

# ============================================================
# MECH — physics/movement carried over from 002, mesh replaced
# with K-12B sprite planes driven by the same leg-phase math.
# ============================================================
class ContinuousMech:
    def __init__(self, cx, cy, gz):
        self.cx, self.cy = float(cx), float(cy)
        self.gz = gz
        self.gx, self.gy = int(round(cx)), int(round(cy))
        self.is_entity = True

        self.velocity = 0.0
        self.max_speed = 4.0
        self.body_facing = 1
        self.com_offset = (0.5, 0.5)
        self.surface_z_offset = 1.0

        self.leg_angle = 0.0
        self.turret_angle = 0.0
        self.leg_slew_speed = 35.0
        self.turret_slew_speed = 75.0

        self.walk_cycle = 0.0
        self.stride_len = 1.0
        self.step_height = 0.4
        self.gait_speed = 5.0
        self.chassis_w = 1.4

        self.euler_stress = 0.0
        self.stress_threshold = 2.0
        self.stagger_vec = [0.0, 0.0, 0.0]
        self.stagger_vel = [0.0, 0.0, 0.0]

        self.hip_check_threshold = 3.0
        self.hip_check_cooldown = 0.0
        self.hip_check_max_lanes = 5

        self.crossleg_timer = 0.0
        self.crossleg_duration = 0.4

        self.team_coherence = 1.0
        self.poise = 1.0

        # Lifted-state per foot, updated each draw() from the same phase
        # math that drives world_foot z. This is the single source of
        # truth both the sprite frame AND the purple-tile flash read from.
        self.left_foot_lifted = False
        self.right_foot_lifted = False

    def process_symbiosis(self, golden_path_matrix):
        if 0 <= self.gx < MAP_W and 0 <= self.gy < MAP_H:
            path_weight = golden_path_matrix[self.gx, self.gy]
            self.team_coherence = 1.0 + (path_weight * 1.5)
            self.poise = 1.0 + (path_weight * 2.0)
        else:
            self.team_coherence = 1.0
            self.poise = 1.0

    def toggle_throttle(self):
        self.euler_stress += 1.2
        self.velocity = self.max_speed if self.velocity == 0 else 0.0

    def reverse_facing(self):
        self.euler_stress += 2.5
        self.body_facing *= -1

    def apply_vector_shock(self, stress_load, force_x, force_y, force_z):
        self.euler_stress += stress_load
        rx, ry, rz = rotate_z(force_x, force_y, force_z, self.leg_angle)
        self.stagger_vel[0] += rx
        self.stagger_vel[1] += ry
        self.stagger_vel[2] += rz

    def get_foot_positions(self, target_cy):
        l_gy = int(math.floor((target_cy + 1.0) / 2.0) * 2)
        r_gy = int(math.floor(target_cy / 2.0) * 2) + 1
        return l_gy, r_gy

    def can_move(self, target_gx, target_gy, target_cy, grid_map):
        l_gy, r_gy = self.get_foot_positions(target_cy)
        cells_to_check = [(target_gx, target_gy), (target_gx - 1, l_gy), (target_gx + 1, r_gy)]
        for fx, fy in cells_to_check:
            if not (0 <= fx < MAP_W and 0 <= fy < MAP_H): return False
            if grid_map[fx][fy].btype == 'chasm': return False
        return True

    def strafe(self, direction, cause, grid_map):
        lanes = min(self.hip_check_max_lanes,
                    1 + int(abs(self.stagger_vel[0]) / self.hip_check_threshold))

        l_gy, r_gy = self.get_foot_positions(self.cy)
        landing_foot_gy = r_gy if direction > 0 else l_gy

        landed_gx = self.gx
        for step in range(1, lanes + 1):
            target_gx = self.gx + direction * step
            if not (0 <= target_gx < MAP_W) or not (0 <= landing_foot_gy < MAP_H): break
            cells_to_check = [(target_gx, self.gy), (target_gx, landing_foot_gy)]
            if any(grid_map[fx][fy].btype == 'chasm' for fx, fy in cells_to_check): break
            landed_gx = target_gx

        if landed_gx == self.gx: return False
        self.gx = landed_gx
        self.cx = float(landed_gx)
        self.stagger_vel[0] *= 0.3
        self.hip_check_cooldown = 0.35
        self.crossleg_timer = self.crossleg_duration
        return True

    def process_overflow_stagger(self, dt, grid_map):
        if self.hip_check_cooldown > 0.0: self.hip_check_cooldown -= dt

        effective_threshold = self.stress_threshold * self.team_coherence

        if self.euler_stress > effective_threshold:
            overflow = self.euler_stress - effective_threshold
            self.stagger_vel[0] += random.uniform(-0.5, 0.5) * overflow
            self.stagger_vel[1] += random.uniform(-0.5, 0.5) * overflow
            self.stagger_vel[2] += random.uniform(-0.2, 0.8) * overflow
            self.euler_stress = 0.0

            if self.hip_check_cooldown <= 0.0 and abs(self.stagger_vel[0]) > self.hip_check_threshold:
                direction = 1 if self.stagger_vel[0] > 0 else -1
                self.strafe(direction, StrafeCause.RECOIL_OVERFLOW, grid_map)

        spring_constant = 18.0
        damping_factor = 4.5
        for i in range(3):
            self.stagger_vec[i] += self.stagger_vel[i] * dt
            spring_force = -self.stagger_vec[i] * spring_constant
            damping_force = -self.stagger_vel[i] * damping_factor
            acceleration = spring_force + damping_force
            self.stagger_vel[i] += acceleration * dt

    def update(self, dt, grid_map, golden_path_matrix):
        self.process_symbiosis(golden_path_matrix)

        self.leg_angle = (self.leg_angle + self.leg_slew_speed * dt) % 360.0
        stable_slew = self.turret_slew_speed / self.poise
        self.turret_angle = (self.turret_angle - stable_slew * dt) % 360.0

        if self.crossleg_timer > 0.0: self.crossleg_timer = max(0.0, self.crossleg_timer - dt)

        if self.velocity > 0:
            self.euler_stress += (0.1 / self.team_coherence) * dt
            self.walk_cycle += dt * self.gait_speed

            dy = self.body_facing * self.velocity * dt
            next_cy = self.cy + dy
            next_gy = int(round(next_cy))

            if self.can_move(self.gx, next_gy, next_cy, grid_map):
                self.cy = next_cy
                self.gy = next_gy
            else:
                self.velocity = 0.0
                self.euler_stress += 2.0

        self.process_overflow_stagger(dt, grid_map)

    def apply_highlights(self, grid_map):
        if 0 <= self.gx < MAP_W and 0 <= self.gy < MAP_H:
            grid_map[self.gx][self.gy].highlight = 'yellow'
        l_gy, r_gy = self.get_foot_positions(self.cy)
        if 0 <= self.gx - 1 < MAP_W and 0 <= l_gy < MAP_H:
            grid_map[self.gx - 1][l_gy].highlight = 'purple_lifted' if self.left_foot_lifted else 'purple'
        if 0 <= self.gx + 1 < MAP_W and 0 <= r_gy < MAP_H:
            grid_map[self.gx + 1][r_gy].highlight = 'purple_lifted' if self.right_foot_lifted else 'purple'

    def calculate_leg_geometry(self, side_sign, phase_offset, base_cx, base_cy, com_swing_z):
        """Unchanged from 002: this is still the authority on where each
        foot is in 3D and whether it's lifted off the ground (local_fz > 0)."""
        local_hx, local_hy, local_hz = side_sign * (self.chassis_w / 2.0), 0.0, 1.2 + com_swing_z
        phase = (self.walk_cycle + phase_offset) % (2 * math.pi)

        if phase < math.pi:
            t = phase / math.pi
            local_fy = (self.stride_len / 2.0) - (t * self.stride_len)
            local_fz = math.sin(phase) * self.step_height
        else:
            t = (phase - math.pi) / math.pi
            local_fy = -(self.stride_len / 2.0) + (t * self.stride_len)
            local_fz = 0.0

        local_fx = local_hx
        if self.crossleg_timer > 0.0:
            t = 1.0 - (self.crossleg_timer / self.crossleg_duration)
            local_fx = local_hx - math.sin(math.pi * t) * (local_hx * 1.6)

        hx, hy, hz = rotate_z(local_hx, local_hy, local_hz, self.leg_angle)
        fx, fy, fz = rotate_z(local_fx, local_fy, local_fz, self.leg_angle)

        world_hip = (base_cx + hx, base_cy + hy, self.gz + self.surface_z_offset + hz)
        world_foot = (base_cx + fx, base_cy + fy, self.gz + self.surface_z_offset + fz)
        kx_offset, ky_offset, _ = rotate_z(side_sign * 0.3, -0.2, 0.0, self.leg_angle)
        world_knee = ((world_hip[0] + world_foot[0]) / 2.0 + kx_offset,
                      (world_hip[1] + world_foot[1]) / 2.0 + ky_offset,
                      (world_hip[2] + world_foot[2]) / 2.0 + 0.1)

        return world_hip, world_knee, world_foot, local_fz

    def draw(self, surface, cam_x, cam_y):
        base_cx = self.cx + self.com_offset[0] + self.stagger_vec[0]
        base_cy = self.cy + self.com_offset[1] + self.stagger_vec[1]
        com_swing_z = self.stagger_vec[2]

        # Left = side_sign -1, phase_offset 0.0 (matches 002's leg[0])
        # Right = side_sign +1, phase_offset pi (matches 002's leg[1])
        l_hip, l_knee, l_foot, l_fz = self.calculate_leg_geometry(-1, 0.0, base_cx, base_cy, com_swing_z)
        r_hip, r_knee, r_foot, r_fz = self.calculate_leg_geometry(1, math.pi, base_cx, base_cy, com_swing_z)

        lift_threshold = self.step_height * 0.15
        self.left_foot_lifted = l_fz > lift_threshold
        self.right_foot_lifted = r_fz > lift_threshold

        # --- pick leg sprite frame from the SAME phase math driving the tiles ---
        if self.velocity > 0:
            if self.left_foot_lifted and not self.right_foot_lifted:
                leg_key = "KICK_A"
            elif self.right_foot_lifted and not self.left_foot_lifted:
                leg_key = "KICK_B"
            else:
                leg_key = "STANCE"
        else:
            leg_key = "WIDE"

        # --- arms: idle wiggle while walking, raised when staggered hard, neutral when still ---
        stagger_mag = math.sqrt(self.stagger_vec[0]**2 + self.stagger_vec[1]**2)
        if stagger_mag > 0.4:
            arm_key = "ARMS_RAISED"
        elif self.velocity > 0:
            arm_key = "ARMS_WIGGLE_A" if self.left_foot_lifted else "ARMS_WIGGLE_B"
        else:
            arm_key = "ARMS_NEUTRAL"

        # --- compose K-12B sprite ---
        active_front = TRUNK_FRONT.copy()
        active_front.blit(LEG_FRAMES[leg_key], (0, 0))
        active_front.blit(ARM_FRAMES[arm_key], (0, 0))

        # --- perspective squash driven by turret_angle (the mesh's old yaw) ---
        angle_rad = math.radians(self.turret_angle)
        f_cos = math.cos(angle_rad)
        s_cos = math.cos(angle_rad + math.pi / 2)

        f_scale_x = max(int(abs(f_cos) * FRAME_W * 0.55), 1)
        s_scale_x = max(int(abs(s_cos) * FRAME_W * 0.55), 1)
        scale_y = int(FRAME_H * 0.55)

        f_proj = pygame.transform.scale(active_front, (f_scale_x, scale_y))
        s_proj = pygame.transform.scale(TRUNK_SIDE, (s_scale_x, scale_y))

        # --- anchor sprite at COM (base_cx, base_cy) projected into iso space ---
        chassis_base_z = self.gz + self.surface_z_offset + 1.2 + com_swing_z
        anchor_iso_x, anchor_iso_y = project_iso(base_cx, base_cy, chassis_base_z)
        rx = cam_x + anchor_iso_x
        ry = cam_y + anchor_iso_y

        if f_cos >= 0:
            if s_cos >= 0:
                surface.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
                surface.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))
            else:
                surface.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))
                surface.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
        else:
            if s_cos >= 0:
                surface.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))
                surface.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
            else:
                surface.blit(s_proj, (rx - s_scale_x // 2, ry - scale_y // 2))
                surface.blit(f_proj, (rx - f_scale_x // 2, ry - scale_y // 2))

        # --- small ground-contact markers at actual foot world positions,
        # so the physics feet and the sprite feet can be visually cross-checked ---
        for foot, lifted in [(l_foot, self.left_foot_lifted), (r_foot, self.right_foot_lifted)]:
            fx_screen = cam_x + project_iso(*foot)[0]
            fy_screen = cam_y + project_iso(*foot)[1]
            color = (255, 230, 80) if lifted else (255, 60, 60)
            pygame.draw.circle(surface, color, (int(fx_screen), int(fy_screen)), 5)

# --- 生成 (World Generation) ---
grid_data = [[StaticBlock(x, y, 1, 'grass') for y in range(MAP_H)] for x in range(MAP_W)]
for x in range(MAP_W):
    for y in range(MAP_H):
        if y % 18 == 0 and x < 4: grid_data[x][y] = StaticBlock(x, y, -1, 'chasm')

slime_matrix = np.random.rand(MAP_W, MAP_H) * 0.25
golden_path_matrix = np.zeros((MAP_W, MAP_H))

player = ContinuousMech(cx=6.0, cy=4.0, gz=1)
carver = AutoCarver(start_x=7, start_y=5)
font = pygame.font.SysFont("monospace", 14, bold=True)
hud_font = pygame.font.SysFont("monospace", 20, bold=True)
big_hud_font = pygame.font.SysFont("monospace", 28, bold=True)

# --- 実行 (Execution Loop) ---
running = True
slime_timer = 0.0

while running:
    dt = clock.tick(60) / 1000.0

    slime_timer += dt
    if slime_timer > 0.15:
        slime_timer = 0.0
        slime_matrix = creep_slime(slime_matrix)

    golden_path_matrix *= 0.99
    carver.update(dt, slime_matrix, golden_path_matrix)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if BTN_STRAFE_L.collidepoint(event.pos):
                player.strafe(-1, StrafeCause.MANUAL, grid_data)
            elif BTN_STRAFE_R.collidepoint(event.pos):
                player.strafe(1, StrafeCause.MANUAL, grid_data)
            elif BTN_REV.collidepoint(event.pos):
                player.reverse_facing()
            elif BTN_THR.collidepoint(event.pos):
                player.toggle_throttle()
            elif BTN_SHOCK_L_SHOULDER.collidepoint(event.pos):
                player.apply_vector_shock(1.5, 2.5, -0.5, -0.5)
            elif BTN_SLIP_R_FOOT.collidepoint(event.pos):
                player.apply_vector_shock(2.0, 1.0, 2.5, -1.8)
            elif BTN_CORE_IMPACT.collidepoint(event.pos):
                player.apply_vector_shock(4.0, 0.0, -1.0, -3.5)

    for x in range(MAP_W):
        for y in range(MAP_H):
            grid_data[x][y].path_weight = golden_path_matrix[x, y]

    player.update(dt, grid_data, golden_path_matrix)

    for row in grid_data:
        for block in row: block.highlight = None
    player.apply_highlights(grid_data)

    screen.fill((10, 12, 18))

    p_iso_x, p_iso_y = project_iso(player.cx + player.com_offset[0] + player.stagger_vec[0],
                                   player.cy + player.com_offset[1] + player.stagger_vec[1],
                                   player.gz)
    camera_x, camera_y = (WIDTH // 2) - p_iso_x, (HEIGHT // 2) - p_iso_y + (TILE_H // 2)

    render_list = [grid_data[x][y] for x in range(max(0, player.gx-10), min(MAP_W, player.gx+10))
                   for y in range(max(0, player.gy-15), min(MAP_H, player.gy+15))]

    for obj in sorted(render_list + [player], key=lambda o: (o.gx + o.gy, o.gz, getattr(o, 'is_entity', False))):
        obj.draw(screen, camera_x, camera_y)

    # --- UI Rendering ---
    pygame.draw.rect(screen, (30, 80, 160), BTN_STRAFE_L, border_radius=8)
    pygame.draw.rect(screen, (60, 120, 220), BTN_STRAFE_L, 3, border_radius=8)
    screen.blit(big_hud_font.render("<< STRAFE (左)", True, (255, 255, 255)), (BTN_STRAFE_L.x + 35, BTN_STRAFE_L.y + 32))

    pygame.draw.rect(screen, (30, 80, 160), BTN_STRAFE_R, border_radius=8)
    pygame.draw.rect(screen, (60, 120, 220), BTN_STRAFE_R, 3, border_radius=8)
    screen.blit(big_hud_font.render("STRAFE (右) >>", True, (255, 255, 255)), (BTN_STRAFE_R.x + 35, BTN_STRAFE_R.y + 32))

    pygame.draw.rect(screen, (70, 70, 90), BTN_REV)
    screen.blit(font.render("REVERSE (Y)", True, (255, 255, 255)), (BTN_REV.x + 30, BTN_REV.y + 18))

    thr_color = (40, 140, 40) if player.velocity > 0 else (140, 40, 40)
    pygame.draw.rect(screen, thr_color, BTN_THR)
    screen.blit(font.render("THROTTLE", True, (255, 255, 255)), (BTN_THR.x + 45, BTN_THR.y + 18))

    pygame.draw.rect(screen, (120, 60, 60), BTN_SHOCK_L_SHOULDER)
    screen.blit(font.render("SHOCK: L-SHOULDER", True, (255, 200, 200)), (BTN_SHOCK_L_SHOULDER.x + 20, BTN_SHOCK_L_SHOULDER.y + 18))

    pygame.draw.rect(screen, (140, 90, 40), BTN_SLIP_R_FOOT)
    screen.blit(font.render("SLIP: R-FOOT", True, (255, 220, 180)), (BTN_SLIP_R_FOOT.x + 20, BTN_SLIP_R_FOOT.y + 18))

    pygame.draw.rect(screen, (160, 40, 40), BTN_CORE_IMPACT)
    screen.blit(font.render("IMPACT: CORE", True, (255, 180, 180)), (BTN_CORE_IMPACT.x + 20, BTN_CORE_IMPACT.y + 18))

    coh_color = (100, 255, 150) if player.team_coherence > 1.2 else (200, 200, 200)
    pos_color = (100, 200, 255) if player.poise > 1.5 else (200, 200, 200)

    screen.blit(hud_font.render(f"TEAM-COHERENCE: {player.team_coherence:.2f}x", True, coh_color), (20, 20))
    screen.blit(hud_font.render(f"POISE (FINESSE): {player.poise:.2f}x", True, pos_color), (20, 50))
    foot_state = f"L:{'UP' if player.left_foot_lifted else 'down'}  R:{'UP' if player.right_foot_lifted else 'down'}"
    screen.blit(hud_font.render(f"FOOT SYNC: {foot_state}", True, (230, 120, 255)), (20, 80))

    pygame.display.flip()

pygame.quit()
sys.exit()
