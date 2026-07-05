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
pygame.display.set_caption("Protocol VIPER: Cactuar Symbiotic Evasion Vectors")
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
# CACTUAR SPRITE PLANES (carried over from cactuar_solo.py)
# ============================================================
COLOR_CACTUS = (40, 190, 80)
COLOR_CACTUS_SHADOW = (20, 100, 45)
COLOR_FACE = (15, 15, 15)

def create_trunk_plane(w, h):
    """Static torso + face plane. Arms/legs are swapped in separately."""
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
    """Bakes specific arm poses to hot-swap independently of legs."""
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
    """Bakes specific leg poses to hot-swap independently of arms.
    STANCE = both feet grounded. KICK_A = LEFT foot lifted. KICK_B = RIGHT foot lifted."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    base_y = h - 100

    if frame_type == "STANCE":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 22, base_y, 16, 60))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 6, base_y, 16, 60))
    elif frame_type == "KICK_A":  # left leg lifted forward
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 30, base_y - 10, 16, 50))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, base_y + 30, 40, 14))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 10, base_y + 5, 16, 55))
    elif frame_type == "KICK_B":  # right leg lifted forward
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 26, base_y + 5, 16, 55))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 14, base_y - 10, 16, 50))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 14, base_y + 30, 40, 14))
    elif frame_type == "WIDE":
        pygame.draw.rect(surf, COLOR_CACTUS, (cx - 40, base_y, 16, 60))
        pygame.draw.rect(surf, COLOR_CACTUS, (cx + 24, base_y, 16, 60))
    return surf

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
}

# ============================================================
# MECH — physics/movement carried over from 002, mesh replaced
# with cactuar sprite planes driven by the same leg-phase math.
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

        # --- arms: idle wiggle while walking, up when staggered hard, out when still ---
        stagger_mag = math.sqrt(self.stagger_vec[0]**2 + self.stagger_vec[1]**2)
        if stagger_mag > 0.4:
            arm_key = "ARMS_UP"
        elif self.velocity > 0:
            arm_key = "ARMS_WIGGLE_A" if self.left_foot_lifted else "ARMS_WIGGLE_B"
        else:
            arm_key = "ARMS_OUT"

        # --- compose cactuar sprite ---
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
