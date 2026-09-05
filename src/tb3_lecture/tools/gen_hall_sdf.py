#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the campus multi-function-hall world v3.

Layout follows a press-conference / auditorium:
  - stage + projection screen on the FRONT (+x) wall
  - a SIDE door on the right wall (near the back), robot enters and must travel
    up the right-hand aisle, then turn 90 deg into the central aisle and on to
    the presentation spot in front of the stage  => non-trivial path
  - dense individual small chairs in two stepped audience blocks (5+4 chairs
    per row x 8 rows each side of a central aisle), aisle corridor along the
    right wall for the robot
  - two walking actors near the back / left margin as moving "attendees"

Robot spawn / goal stay on the flat aisles so 2D SLAM navigation is easy.
"""

import os
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, '..'))

# --- hall --------------------------------------------------------------------
WID, LEN, H_WALL, T = 8.0, 10.0, 2.6, 0.15
DOOR_X = 1.9          # centre of the side door on the right wall
DOOR_HALF = 0.45

# --- audience grid -------------------------------------------------------------
ROW_PITCH = 0.72
ROW_START, ROW_END = 1.55, 6.6        # rows exist in this x band (facing +x)
SEAT_PITCH = 0.5                       # chair spacing along y
PAD_HI, PAD_LO, PAD_STEP = 0.34, 0.0, 0.045   # tier slope: back rows higher
# blocks in y (seats face +x = stage):
L_Y0, L_Y1 = 1.15, 3.30                # left audience block
R_Y0, R_Y1 = 4.70, 6.50                # right audience block
AISLE_MID = 4.05                       # centre aisle around y = 4.05
COR_Y0 = 6.60                          # robot corridor along the right wall

# --- front / stage -------------------------------------------------------------
FRONT_BAND_X = 7.0                     # open transverse band starts here
STAGE_X0, STAGE_X1, STAGE_Y0, STAGE_Y1 = 8.7, 9.95, 0.6, 7.4
PODIUM = (9.3, 2.0)
MEDIA = [(7.9, 5.8), (8.05, 2.0)]      # decor obstacles near the stage (off the aisle)
# world-frame waypoints the robot follows so it does not cut diagonally across
# unmapped seats: along the right corridor, then to the stage front
VIA_WORLD = [{'x': 6.7, 'y': 7.0, 'yaw': 0.0}]

SPAWN = {'x': DOOR_X, 'y': 7.0, 'z': 0.01, 'yaw': 0.0}       # inside side door, faces +x
GOAL = {'x': 7.2, 'y': AISLE_MID, 'yaw': 3.141592653589793}  # stage front centre, faces audience

# --- materials ------------------------------------------------------------------
WALL = (0.84, 0.85, 0.87); DOORF = (0.16, 0.16, 0.18); FLOOR = (0.60, 0.47, 0.34)
PAD = (0.74, 0.71, 0.66)
SEATBACK = (0.10, 0.14, 0.34); SEAT = (0.20, 0.28, 0.52)
STAGE = (0.32, 0.17, 0.10); PODC = (0.42, 0.34, 0.26); SCREEN = (0.10, 0.10, 0.12)
MEDC = (0.55, 0.50, 0.46)


def mat(rgb):
    r, g, b = rgb
    return (f'<material><ambient>{r} {g} {b} 1</ambient>'
            f'<diffuse>{r} {g} {b} 1</diffuse></material>')


def box(name, cx, cy, sx, sy, sz, zc, rgb):
    return f'''    <link name='{name}'>
      <pose>0 0 0 0 0 0</pose>
      <collision name='{name}_col'>
        <pose>{cx:.4f} {cy:.4f} {zc:.4f} 0 0 0</pose>
        <geometry><box><size>{sx:.4f} {sy:.4f} {sz:.4f}</size></box></geometry>
        <surface><friction><ode><mu>0.7</mu><mu2>0.7</mu2></ode></friction></surface>
      </collision>
      <visual name='{name}_vis'>
        <pose>{cx:.4f} {cy:.4f} {zc:.4f} 0 0 0</pose>
        <geometry><box><size>{sx:.4f} {sy:.4f} {sz:.4f}</size></box></geometry>
        {mat(rgb)}
      </visual>
    </link>
'''


def cylinder(name, cx, cy, radius, h, zc, rgb):
    return f'''    <link name='{name}'>
      <pose>0 0 0 0 0 0</pose>
      <collision name='{name}_col'>
        <pose>{cx:.4f} {cy:.4f} {zc:.4f} 0 0 0</pose>
        <geometry><cylinder><radius>{radius}</radius><length>{h}</length></cylinder></geometry>
      </collision>
      <visual name='{name}_vis'>
        <pose>{cx:.4f} {cy:.4f} {zc:.4f} 0 0 0</pose>
        <geometry><cylinder><radius>{radius}</radius><length>{h}</length></cylinder></geometry>
        {mat(rgb)}
      </visual>
    </link>
'''


def chair(name, cx, cy, h):
    """Individual small chair standing on a pad of top height h."""
    out = []
    # backrest (behind, -x side), facing +x
    out.append(box(name + '_back', cx - 0.08, cy, 0.07, 0.40, 0.52, h + 0.58, SEATBACK))
    # cushion
    out.append(box(name + '_seat', cx + 0.02, cy, 0.16, 0.40, 0.10, h + 0.37, SEAT))
    return '\n'.join(out)


def build_parts():
    p = []

    # ---- walls: back, front, left full; right wall split by side door -------
    p.append(box('wall_back', 0 - T / 2, WID / 2, T, WID + 2 * T, H_WALL, H_WALL / 2, WALL))
    p.append(box('wall_front', LEN + T / 2, WID / 2, T, WID + 2 * T, H_WALL, H_WALL / 2, WALL))
    p.append(box('wall_left', LEN / 2, -T / 2, LEN + 2 * T, T, H_WALL, H_WALL / 2, WALL))
    # right wall y = WID; gap around x = DOOR_X
    x0, x1 = DOOR_X - DOOR_HALF, DOOR_X + DOOR_HALF
    p.append(box('wall_right_a', (0 + x0) / 2, WID + T / 2, x0, T, H_WALL, H_WALL / 2, WALL))
    p.append(box('wall_right_b', (x1 + LEN) / 2, WID + T / 2, LEN - x1, T, H_WALL, H_WALL / 2, WALL))
    for xj in (x0, x1):
        p.append(box('door_jamb_%s' % str(xj).replace('.', '_'), xj, WID + T / 2,
                     0.08, 0.12, H_WALL, H_WALL / 2, DOORF))
    # floor
    p.append(box('floor', LEN / 2, WID / 2, LEN, WID, 0.02, 0.005, FLOOR))

    # ---- dense stepped audience: rows along x, chairs in two y-blocks ------
    xrow = ROW_START
    r = 0
    rows = []
    while xrow <= ROW_END:
        rows.append(xrow)
        xrow += ROW_PITCH
    n = len(rows)
    for r, xr in enumerate(rows):
        padh = PAD_HI - (n - 1 - r) * PAD_STEP
        padh = max(padh, PAD_LO)
        # tier pad under each block (not under aisles)
        p.append(box(f'padL{r}', xr, (L_Y0 + L_Y1) / 2, ROW_PITCH - 0.10,
                     L_Y1 - L_Y0 + 0.2, padh, padh / 2, PAD))
        p.append(box(f'padR{r}', xr, (R_Y0 + R_Y1) / 2, ROW_PITCH - 0.10,
                     R_Y1 - R_Y0 + 0.2, padh, padh / 2, PAD))
        c = 0
        y = L_Y0 + SEAT_PITCH / 2
        while y <= L_Y1:
            p.append(chair(f'chL{r}_{c}', xr, y, padh))
            y += SEAT_PITCH
            c += 1
        c = 0
        y = R_Y0 + SEAT_PITCH / 2
        while y <= R_Y1:
            p.append(chair(f'chR{r}_{c}', xr, y, padh))
            y += SEAT_PITCH
            c += 1

    # ---- stage + step + podium + screen ----
    p.append(box('stage', (STAGE_X0 + STAGE_X1) / 2, (STAGE_Y0 + STAGE_Y1) / 2,
                 STAGE_X1 - STAGE_X0, STAGE_Y1 - STAGE_Y0, 0.16, 0.08, STAGE))
    p.append(box('stage_step', STAGE_X0 - 0.08, (STAGE_Y0 + STAGE_Y1) / 2,
                 0.16, STAGE_Y1 - STAGE_Y0, 0.08, 0.04, STAGE))
    px, py = PODIUM
    p.append(box('podium', px, py, 0.6, 0.7, 0.9, 0.45, PODC))
    p.append(box('screen', LEN - 0.02, WID / 2, 0.02, 3.4, 1.7, 1.8, SCREEN))

    # decor obstacles in the front band (media pedestals / plants)
    for i, (mx, my) in enumerate(MEDIA):
        p.append(box(f'media{i}', mx, my, 0.6, 0.45, 0.8, 0.4, MEDC))
    return '\n'.join(p)


def model_sdf():
    return f'''<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="lecture_hall">
    <static>true</static>
    <pose>0 0 0 0 0 0</pose>
{build_parts()}  </model>
</sdf>
'''


def actor(name, pts, delay, spd=0.45):
    wps, t = [], 0.0
    for k, (x, y, yaw) in enumerate(pts):
        wps.append(f'          <waypoint>\n            <time>{t:.2f}</time>\n'
                   f'            <pose>{x} {y} 1.0 0 0 {yaw}</pose>\n          </waypoint>')
        if k < len(pts) - 1:
            dx, dy = pts[k + 1][0] - x, pts[k + 1][1] - y
            t += (dx * dx + dy * dy) ** 0.5 / spd
    t += 5.0
    wps.append(f'          <waypoint>\n            <time>{t:.2f}</time>\n'
               f'            <pose>{pts[0][0]} {pts[0][1]} 1.0 0 0 {pts[0][2]}</pose>\n'
               '          </waypoint>')
    return f'''    <actor name="{name}">
      <skin>
        <filename>https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae</filename>
        <scale>1.0</scale>
      </skin>
      <animation name="walk">
        <filename>https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae</filename>
        <scale>1.0</scale>
        <interpolate_x>true</interpolate_x>
      </animation>
      <script>
        <loop>true</loop>
        <delay_start>{delay:.1f}</delay_start>
        <auto_start>true</auto_start>
        <trajectory id="0" type="walk" tension="0.6">
{chr(10).join(wps)}
        </trajectory>
      </script>
    </actor>
'''


def world_sdf():
    a1 = actor('attendee_a',
               [(5.2, 0.7, 0), (6.6, 0.7, 0), (6.6, 0.7, 90), (6.6, 1.6, 90),
                (6.6, 1.6, 180), (5.2, 1.6, 180), (5.2, 1.6, 270), (5.2, 0.7, 0)],
               delay=2.0)
    a2 = actor('attendee_b',
               [(0.6, 2.2, 0), (0.6, 5.0, 0), (0.6, 5.0, 180), (0.6, 2.2, 180), (0.6, 2.2, 0)],
               delay=12.0, spd=0.3)
    return f'''<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="lecture_hall">
    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>

    <include>
      <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Ground Plane</uri>
    </include>
    <include>
      <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Sun</uri>
    </include>

    <model name="lecture_hall">
      <static>true</static>
      <include>
        <uri>model://lecture_hall</uri>
      </include>
    </model>

{a1}
{a2}
  </world>
</sdf>
'''


def model_config():
    return f'''<?xml version="1.0" ?>
<model>
  <name>Lecture Hall (多功能厅) v3</name>
  <version>3.0</version>
  <sdf version="1.8">model.sdf</sdf>
  <author><name>chilhoho</name></author>
  <description>
    Auditorium-style multi-function hall {LEN:.0f}x{WID:.0f} m: dense stepped
    audience chairs (8 rows x two blocks), side door on the right wall, front
    stage with podium + screen, two walking actors.
  </description>
</model>
'''


def main():
    base = os.path.join(PKG, 'models', 'lecture_hall')
    os.makedirs(base, exist_ok=True)
    os.makedirs(os.path.join(PKG, 'worlds'), exist_ok=True)
    os.makedirs(os.path.join(PKG, 'config'), exist_ok=True)
    open(os.path.join(base, 'model.sdf'), 'w').write(model_sdf())
    open(os.path.join(base, 'model.config'), 'w').write(model_config())
    open(os.path.join(PKG, 'worlds', 'lecture_hall.world'), 'w').write(world_sdf())
    yaml.safe_dump({'hall': {'len': LEN, 'width': WID},
                    'robot_model': 'waffle_pi',
                    'start_door': SPAWN,
                    'via_world': VIA_WORLD,
                    'goal_podium': GOAL},
                   open(os.path.join(PKG, 'config', 'podium.yaml'), 'w'),
                   sort_keys=False, allow_unicode=True)
    print('wrote v3 world/model/config')


if __name__ == '__main__':
    main()
