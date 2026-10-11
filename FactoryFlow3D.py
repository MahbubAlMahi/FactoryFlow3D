from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math
import random


WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 800

camera_pos = (700, 700, 700)
camera_angle = 45
camera_height = 700
camera_distance = 1050
camera_mode = 0
fovY = 120


GRID_LENGTH = 700
factory_width = 1400
factory_height = 1400


quadric = None


robot_x = -250
robot_y = 100
robot_z = 0

base_angle = 270
shoulder_angle = 50
elbow_angle = 45
wrist_angle = 0

BASE_HEIGHT = 78
UPPER_ARM_LENGTH = 85
FOREARM_LENGTH = 75
WRIST_LENGTH = 35

gripper_open = True
automatic_mode = True
held_package_id = None

auto_arm_state = "home"
auto_package_id = None
arm_wait = 0

target_base_angle = 270
target_shoulder_angle = 50
target_elbow_angle = 45
target_wrist_angle = 0


CONVEYOR_START_X = -620
CONVEYOR_END_X = -250
CONVEYOR_Y = -50
INSPECTION_X = -430
PACKAGE_Z = 49

GOOD_DOCK = (-100, 100, 46)
BAD_BIN = (-250, 250, 46)

packages = []
next_package_id = 1
spawn_counter = 0
belt_offset = 0

inspection_flash = 0
last_inspection_defective = False
inspected_packages = 0
sorted_packages = 0
rejected_packages = 0
escaped_defects = 0

jam_active = False
jam_pressure = 0
jam_damage_counter = 0
emergency_stop = False


SORT_DOCK = (-100, 100)
WAREHOUSE_DOCK = (420, 100)
LOADING_DOCK = (420, 440)

agv_x = SORT_DOCK[0]
agv_y = SORT_DOCK[1]
agv_angle = 0
agv_job = "idle"
agv_route = []
agv_route_index = 0
agv_cargo_type = None
agv_cargo_id = None
agv_blocked = False

barrier_active = False
BARRIER_X = 150
BARRIER_Y = 100

storage_inventory = 0
storage_capacity = 12
stored_packages = 0
pending_orders = 0
orders_fulfilled = 0
missed_orders = 0
order_timer = 0
order_wait_timer = 0
loading_flash = 0


score = 0
factory_health = 100
shift_seconds = 180
clock_counter = 0
simulation_frame = 0

ORDER_TARGET = 6
SHIFT_LIMIT = 180
defect_chance = 0.30
difficulty_level = "NORMAL"
difficulty_selected = False
game_over = False
game_won = False

status_message = "Factory started - automatic production is active"
status_timer = 240


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def distance_2d(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def distance_3d(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x2 - x1) ** 2 +
                     (y2 - y1) ** 2 +
                     (z2 - z1) ** 2)


def move_towards(current, target, speed):
    if abs(target - current) <= speed:
        return target
    if target > current:
        return current + speed
    return current - speed


def angle_difference(current, target):
    return (target - current + 180) % 360 - 180


def move_angle_towards(current, target, speed):
    difference = angle_difference(current, target)
    if abs(difference) <= speed:
        return target % 360
    if difference > 0:
        return (current + speed) % 360
    return (current - speed) % 360


def set_message(message, frames=180):
    global status_message, status_timer
    status_message = message
    status_timer = frames


def find_package(package_id):
    for package in packages:
        if package["id"] == package_id:
            return package
    return None


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(x, y)
    for character in str(text):
        glutBitmapCharacter(font, ord(character))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_box(x, y, z, length, width, height, color):
    glPushMatrix()
    glColor3f(color[0], color[1], color[2])
    glTranslatef(x, y, z)
    glScalef(length, width, height)
    glutSolidCube(1)
    glPopMatrix()


def draw_cylinder(radius, height, color):
    glColor3f(color[0], color[1], color[2])
    gluCylinder(quadric, radius, radius, height, 12, 4)


def draw_sphere(radius, color):
    glColor3f(color[0], color[1], color[2])
    gluSphere(quadric, radius, 12, 12)


def draw_floor_rectangle(x1, y1, x2, y2, z, color):
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    glVertex3f(x1, y1, z)
    glVertex3f(x2, y1, z)
    glVertex3f(x2, y2, z)
    glVertex3f(x1, y2, z)
    glEnd()


def draw_arm_segment(length, thickness, color):
    draw_box(length / 2, 0, 0, length, thickness, thickness, color)


def draw_factory_floor():

    tile_size = 50
    glBegin(GL_QUADS)
    for x in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
        for y in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
            if ((x // tile_size) + (y // tile_size)) % 2 == 0:
                glColor3f(0.13, 0.16, 0.19)
            else:
                glColor3f(0.16, 0.19, 0.22)

            glVertex3f(x, y, -3)
            glVertex3f(x + tile_size, y, -3)
            glVertex3f(x + tile_size, y + tile_size, -3)
            glVertex3f(x, y + tile_size, -3)
    glEnd()


    draw_floor_rectangle(-680, -420, -340, -20, -1, (0.18, 0.25, 0.30))
    draw_floor_rectangle(-330, -120, 20, 300, -1, (0.22, 0.22, 0.30))
    draw_floor_rectangle(50, -120, 660, 300, -1, (0.18, 0.27, 0.22))
    draw_floor_rectangle(-680, 340, -360, 650, -1, (0.18, 0.24, 0.34))
    draw_floor_rectangle(-330, 340, 20, 650, -1, (0.29, 0.24, 0.18))
    draw_floor_rectangle(50, 340, 660, 650, -1, (0.28, 0.22, 0.17))


    draw_floor_rectangle(-130, 65, 470, 135, 0, (0.24, 0.30, 0.18))
    draw_floor_rectangle(385, 100, 455, 470, 0, (0.24, 0.30, 0.18))


    for x in range(-100, 451, 80):
        draw_box(x, 100, 2, 35, 5, 3, (0.92, 0.72, 0.12))
    for y in range(160, 451, 75):
        draw_box(420, y, 2, 5, 32, 3, (0.92, 0.72, 0.12))


def draw_factory_walls():
    wall_color = (0.38, 0.43, 0.48)
    wall_height = 55
    wall_thickness = 14


    draw_box(0, -693, wall_height / 2, 1400, wall_thickness,
             wall_height, wall_color)
    draw_box(-695, 0, wall_height / 2, wall_thickness, 1400,
             wall_height, wall_color)
    draw_box(695, 0, wall_height / 2, wall_thickness, 1400,
             wall_height, wall_color)
    draw_box(-430, 693, wall_height / 2, 530, wall_thickness,
             wall_height, wall_color)
    draw_box(590, 693, wall_height / 2, 210, wall_thickness,
             wall_height, wall_color)


    draw_box(-335, -310, wall_height / 2, wall_thickness, 220,
             wall_height, wall_color)
    draw_box(-335, -45, wall_height / 2, wall_thickness, 70,
             wall_height, wall_color)

    draw_box(35, -80, wall_height / 2, wall_thickness, 80,
             wall_height, wall_color)
    draw_box(35, 235, wall_height / 2, wall_thickness, 130,
             wall_height, wall_color)


    draw_box(-540, 320, wall_height / 2, 300, wall_thickness,
             wall_height, wall_color)
    draw_box(-175, 320, wall_height / 2, 210, wall_thickness,
             wall_height, wall_color)
    draw_box(190, 320, wall_height / 2, 250, wall_thickness,
             wall_height, wall_color)
    draw_box(585, 320, wall_height / 2, 150, wall_thickness,
             wall_height, wall_color)


    draw_box(-345, 395, wall_height / 2, wall_thickness, 110,
             wall_height, wall_color)
    draw_box(-345, 580, wall_height / 2, wall_thickness, 140,
             wall_height, wall_color)
    draw_box(35, 395, wall_height / 2, wall_thickness, 110,
             wall_height, wall_color)
    draw_box(35, 580, wall_height / 2, wall_thickness, 140,
             wall_height, wall_color)


def draw_control_room():

    draw_box(-520, 515, 28, 230, 75, 50, (0.16, 0.20, 0.25))
    draw_box(-520, 475, 58, 240, 12, 12, (0.08, 0.10, 0.12))

    screen_colors = [(0.10, 0.75, 0.95),
                     (0.25, 0.90, 0.42),
                     (0.95, 0.58, 0.12)]
    for index in range(3):
        screen_x = -600 + index * 80
        draw_box(screen_x, 508, 92, 66, 9, 52, (0.05, 0.07, 0.09))
        draw_box(screen_x, 501, 92, 55, 3, 40, screen_colors[index])
        draw_box(screen_x, 515, 62, 8, 10, 22, (0.20, 0.23, 0.25))


    draw_box(-620, 440, 35, 50, 50, 65, (0.22, 0.23, 0.25))
    glPushMatrix()
    glTranslatef(-620, 440, 70)
    draw_sphere(15, (0.95, 0.08, 0.08) if emergency_stop
                else (0.12, 0.85, 0.22))
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-405, 555, 0)
    draw_cylinder(7, 105, (0.35, 0.38, 0.40))
    glTranslatef(0, 0, 108)
    draw_sphere(13, (0.95, 0.12, 0.10) if jam_active
                else (0.12, 0.85, 0.24))
    glPopMatrix()


def draw_maintenance_room():

    draw_box(-180, 520, 55, 230, 90, 18, (0.45, 0.30, 0.16))
    for x in (-275, -85):
        for y in (490, 550):
            draw_box(x, y, 27, 12, 12, 54, (0.32, 0.34, 0.35))

    draw_box(-275, 395, 65, 75, 55, 125, (0.25, 0.30, 0.34))
    for level in range(3):
        draw_box(-275, 365, 35 + level * 38, 58, 4, 4,
                 (0.75, 0.78, 0.80))


    for index in range(3):
        glPushMatrix()
        glTranslatef(-235 + index * 55, 515, 66)
        glRotatef(90, 1, 0, 0)
        draw_cylinder(18 - index * 2, 18, (0.20, 0.55, 0.72))
        glPopMatrix()


def draw_loading_bay():

    draw_box(420, 610, 18, 360, 90, 30, (0.32, 0.28, 0.23))
    draw_box(250, 650, 90, 25, 30, 180, (0.42, 0.45, 0.47))
    draw_box(590, 650, 90, 25, 30, 180, (0.42, 0.45, 0.47))

    shutter_height = 45 if loading_flash > 0 else 105
    draw_box(420, 672, 175 - shutter_height / 2,
             315, 10, shutter_height, (0.34, 0.38, 0.41))


    draw_box(510, 535, 55, 185, 85, 80, (0.18, 0.52, 0.82))
    draw_box(385, 535, 45, 80, 82, 62, (0.87, 0.88, 0.90))
    draw_box(378, 494, 58, 55, 4, 28, (0.18, 0.30, 0.42))

    for wheel_x in (405, 550):
        for wheel_y in (490, 580):
            glPushMatrix()
            glTranslatef(wheel_x, wheel_y, 20)
            glRotatef(90, 1, 0, 0)
            draw_cylinder(18, 10, (0.06, 0.06, 0.07))
            glPopMatrix()


    visible_deliveries = min(orders_fulfilled, 5)
    for index in range(visible_deliveries):
        row = index // 3
        column = index % 3
        draw_box(225 + column * 42, 545 + row * 38, 22,
                 34, 30, 38, (0.80, 0.49, 0.20))


def draw_warehouse_racks():
    rack_color = (0.35, 0.40, 0.43)
    shelf_color = (0.48, 0.52, 0.55)

    rack_centers = [175, 340, 505]
    for rack_x in rack_centers:
        for post_x in (rack_x - 65, rack_x + 65):
            for post_y in (220 - 32, 220 + 32):
                draw_box(post_x, post_y, 85, 9, 9, 170, rack_color)

        for shelf_z in (30, 90, 150):
            draw_box(rack_x, 220, shelf_z, 140, 72, 9, shelf_color)

    slot_positions = []
    for rack_x in rack_centers:
        for shelf_z in (57, 117):
            slot_positions.append((rack_x - 35, 220, shelf_z))
            slot_positions.append((rack_x + 35, 220, shelf_z))

    for index in range(min(storage_inventory, storage_capacity)):
        slot = slot_positions[index]
        draw_box(slot[0], slot[1], slot[2], 55, 48, 38,
                 (0.20, 0.72, 0.48))
        draw_box(slot[0], slot[1] - 25, slot[2], 7, 3, 26,
                 (0.93, 0.82, 0.18))


    draw_box(WAREHOUSE_DOCK[0], WAREHOUSE_DOCK[1], 7,
             100, 80, 12, (0.18, 0.56, 0.34))


def draw_conveyor():
    conveyor_length = CONVEYOR_END_X - CONVEYOR_START_X
    conveyor_center = (CONVEYOR_START_X + CONVEYOR_END_X) / 2

    draw_box(conveyor_center, CONVEYOR_Y, 20,
             conveyor_length + 30, 82, 22, (0.19, 0.21, 0.23))
    draw_box(conveyor_center, CONVEYOR_Y, 34,
             conveyor_length, 64, 8, (0.09, 0.11, 0.13))


    for roller_x in range(CONVEYOR_START_X + 10, CONVEYOR_END_X, 35):
        glPushMatrix()
        glTranslatef(roller_x, CONVEYOR_Y + 31, 34)
        glRotatef(90, 1, 0, 0)
        draw_cylinder(9, 62, (0.34, 0.38, 0.41))
        glPopMatrix()

    for index in range(9):
        slat_x = CONVEYOR_START_X + ((index * 46 + belt_offset) %
                                    int(conveyor_length))
        draw_box(slat_x, CONVEYOR_Y, 40, 16, 58, 3,
                 (0.90, 0.66, 0.08))


    for leg_x in range(CONVEYOR_START_X + 30, CONVEYOR_END_X, 90):
        draw_box(leg_x, CONVEYOR_Y - 30, 8, 10, 10, 32,
                 (0.30, 0.32, 0.34))
        draw_box(leg_x, CONVEYOR_Y + 30, 8, 10, 10, 32,
                 (0.30, 0.32, 0.34))


def draw_inspection_scanner():
    scanner_color = (0.12, 0.45, 0.68)
    draw_box(INSPECTION_X, CONVEYOR_Y - 50, 80,
             24, 24, 120, scanner_color)
    draw_box(INSPECTION_X, CONVEYOR_Y + 50, 80,
             24, 24, 120, scanner_color)
    draw_box(INSPECTION_X, CONVEYOR_Y, 145,
             24, 125, 25, scanner_color)

    if inspection_flash > 0:
        beam_color = ((0.95, 0.10, 0.08) if last_inspection_defective
                      else (0.10, 0.92, 0.30))
    else:
        beam_color = (0.12, 0.70, 0.92)

    draw_box(INSPECTION_X + 14, CONVEYOR_Y, 86,
             4, 90, 95, beam_color)

    glPushMatrix()
    glTranslatef(INSPECTION_X, CONVEYOR_Y, 172)
    draw_sphere(12, beam_color)
    glPopMatrix()


def package_color(package):
    if not package["inspected"]:
        return (0.82, 0.54, 0.20)
    if package["defective"]:
        return (0.88, 0.15, 0.12)
    return (0.12, 0.72, 0.48)


def draw_one_package(package):
    color = package_color(package)
    draw_box(package["x"], package["y"], package["z"],
             34, 28, 26, color)
    draw_box(package["x"], package["y"] - 15, package["z"],
             7, 3, 24, (0.94, 0.83, 0.18))


def draw_packages():
    for package in packages:
        draw_one_package(package)


def draw_sorting_bins():

    draw_box(GOOD_DOCK[0], GOOD_DOCK[1], 8,
             110, 90, 15, (0.10, 0.55, 0.28))
    draw_box(GOOD_DOCK[0], GOOD_DOCK[1] + 40, 32,
             110, 10, 45, (0.14, 0.68, 0.34))


    draw_box(BAD_BIN[0], BAD_BIN[1], 7,
             100, 90, 12, (0.52, 0.10, 0.09))
    draw_box(BAD_BIN[0] - 47, BAD_BIN[1], 35,
             8, 90, 65, (0.72, 0.12, 0.10))
    draw_box(BAD_BIN[0] + 47, BAD_BIN[1], 35,
             8, 90, 65, (0.72, 0.12, 0.10))
    draw_box(BAD_BIN[0], BAD_BIN[1] - 42, 35,
             100, 8, 65, (0.72, 0.12, 0.10))
    draw_box(BAD_BIN[0], BAD_BIN[1] + 42, 35,
             100, 8, 65, (0.72, 0.12, 0.10))

    for index in range(min(rejected_packages, 4)):
        draw_box(BAD_BIN[0] - 22 + (index % 2) * 44,
                 BAD_BIN[1] - 15 + (index // 2) * 32,
                 25, 32, 25, 25, (0.82, 0.18, 0.14))


def get_arm_tip():
    base_radian = math.radians(base_angle)
    shoulder_radian = math.radians(shoulder_angle)
    forearm_radian = math.radians(shoulder_angle - elbow_angle)
    wrist_radian = math.radians(shoulder_angle - elbow_angle + wrist_angle)

    radial_distance = (UPPER_ARM_LENGTH * math.cos(shoulder_radian) +
                       FOREARM_LENGTH * math.cos(forearm_radian) +
                       WRIST_LENGTH * math.cos(wrist_radian))

    tip_z = (BASE_HEIGHT +
             UPPER_ARM_LENGTH * math.sin(shoulder_radian) +
             FOREARM_LENGTH * math.sin(forearm_radian) +
             WRIST_LENGTH * math.sin(wrist_radian))

    tip_x = robot_x + radial_distance * math.cos(base_radian)
    tip_y = robot_y + radial_distance * math.sin(base_radian)
    return tip_x, tip_y, tip_z


def draw_robot_arm():
    glPushMatrix()
    glTranslatef(robot_x, robot_y, robot_z)


    draw_cylinder(52, 42, (0.16, 0.35, 0.55))
    glTranslatef(0, 0, 42)
    draw_sphere(40, (0.20, 0.45, 0.70))
    draw_cylinder(27, BASE_HEIGHT - 42, (0.22, 0.50, 0.76))
    glTranslatef(0, 0, BASE_HEIGHT - 42)


    glRotatef(base_angle, 0, 0, 1)
    draw_sphere(24, (0.93, 0.58, 0.10))


    glRotatef(-shoulder_angle, 0, 1, 0)
    draw_arm_segment(UPPER_ARM_LENGTH, 27, (0.88, 0.48, 0.08))
    glTranslatef(UPPER_ARM_LENGTH, 0, 0)
    draw_sphere(20, (0.22, 0.27, 0.31))

    glRotatef(elbow_angle, 0, 1, 0)
    draw_arm_segment(FOREARM_LENGTH, 23, (0.92, 0.56, 0.12))
    glTranslatef(FOREARM_LENGTH, 0, 0)
    draw_sphere(17, (0.22, 0.27, 0.31))

    glRotatef(-wrist_angle, 0, 1, 0)
    draw_arm_segment(WRIST_LENGTH, 18, (0.76, 0.36, 0.07))
    glTranslatef(WRIST_LENGTH, 0, 0)


    draw_box(9, 0, 0, 18, 34, 16, (0.20, 0.22, 0.24))
    finger_gap = 19 if gripper_open else 7
    draw_box(27, finger_gap, 0, 36, 8, 9, (0.82, 0.82, 0.84))
    draw_box(27, -finger_gap, 0, 36, 8, 9, (0.82, 0.82, 0.84))

    glPopMatrix()


    for angle in range(0, 360, 20):
        radian = math.radians(angle)
        marker_x = robot_x + 205 * math.cos(radian)
        marker_y = robot_y + 205 * math.sin(radian)
        draw_box(marker_x, marker_y, 2, 18, 7, 3,
                 (0.92, 0.70, 0.08))


def calculate_arm_angles(target_x, target_y, target_z):
    dx = target_x - robot_x
    dy = target_y - robot_y
    radial_distance = math.sqrt(dx * dx + dy * dy)
    vertical_distance = target_z - BASE_HEIGHT

    first_length = UPPER_ARM_LENGTH
    second_length = FOREARM_LENGTH + WRIST_LENGTH

    reach = math.sqrt(radial_distance ** 2 + vertical_distance ** 2)
    maximum_reach = first_length + second_length - 1
    minimum_reach = abs(first_length - second_length) + 1
    reach = clamp(reach, minimum_reach, maximum_reach)

    cosine_elbow = ((reach ** 2 - first_length ** 2 - second_length ** 2) /
                    (2 * first_length * second_length))
    cosine_elbow = clamp(cosine_elbow, -1, 1)
    calculated_elbow = math.degrees(math.acos(cosine_elbow))

    elbow_radian = math.radians(calculated_elbow)
    calculated_shoulder = math.degrees(
        math.atan2(vertical_distance, radial_distance) +
        math.atan2(second_length * math.sin(elbow_radian),
                   first_length + second_length * math.cos(elbow_radian))
    )

    calculated_base = math.degrees(math.atan2(dy, dx)) % 360

    calculated_shoulder = clamp(calculated_shoulder, -30, 60)
    calculated_elbow = clamp(calculated_elbow, 0, 90)
    return calculated_base, calculated_shoulder, calculated_elbow, 0


def set_arm_target(base, shoulder, elbow, wrist):
    global target_base_angle, target_shoulder_angle
    global target_elbow_angle, target_wrist_angle

    target_base_angle = base % 360
    target_shoulder_angle = clamp(shoulder, -30, 60)
    target_elbow_angle = clamp(elbow, 0, 90)
    target_wrist_angle = clamp(wrist, -90, 90)


def set_arm_target_to_point(point):
    angles = calculate_arm_angles(point[0], point[1], point[2])
    set_arm_target(angles[0], angles[1], angles[2], angles[3])


def move_arm_to_target():
    global base_angle, shoulder_angle, elbow_angle, wrist_angle

    base_angle = move_angle_towards(base_angle, target_base_angle, 1.4)
    shoulder_angle = move_towards(shoulder_angle,
                                  target_shoulder_angle, 0.65)
    elbow_angle = move_towards(elbow_angle, target_elbow_angle, 0.8)
    wrist_angle = move_towards(wrist_angle, target_wrist_angle, 0.9)

    base_ready = abs(angle_difference(base_angle, target_base_angle)) < 0.2
    shoulder_ready = abs(shoulder_angle - target_shoulder_angle) < 0.2
    elbow_ready = abs(elbow_angle - target_elbow_angle) < 0.2
    wrist_ready = abs(wrist_angle - target_wrist_angle) < 0.2
    return base_ready and shoulder_ready and elbow_ready and wrist_ready


def nearest_waiting_package():
    waiting = [package for package in packages
               if package["state"] == "waiting_arm"]
    if not waiting:
        return None
    waiting.sort(key=lambda package: package["id"])
    return waiting[0]


def pick_nearby_package():
    global held_package_id

    tip_x, tip_y, tip_z = get_arm_tip()
    nearest_package = None
    nearest_distance = 100000

    for package in packages:
        if package["state"] != "waiting_arm":
            continue
        current_distance = distance_3d(tip_x, tip_y, tip_z,
                                       package["x"], package["y"],
                                       package["z"])
        if current_distance < nearest_distance:
            nearest_distance = current_distance
            nearest_package = package


    if nearest_package is not None and nearest_distance <= 42:
        nearest_package["state"] = "held"
        held_package_id = nearest_package["id"]
        set_message("Gripper picked package " + str(held_package_id))
        return True

    set_message("Pickup failed - move the gripper closer to the package")
    return False


def finish_sorting(package, selected_bin):
    global held_package_id, score, factory_health
    global sorted_packages, rejected_packages, escaped_defects

    correct_bin = ((package["defective"] and selected_bin == "bad") or
                   (not package["defective"] and selected_bin == "good"))

    sorted_packages += 1
    held_package_id = None

    if correct_bin:
        score += 12
        set_message("Correct classification - package sorted")
    else:
        score -= 15
        factory_health = max(0, factory_health - 12)
        set_message("Wrong bin selected - health and score reduced")

    if selected_bin == "good":
        if package["defective"]:
            escaped_defects += 1

        queue_size = len([item for item in packages
                          if item["state"] == "ready_agv"])
        package["state"] = "ready_agv"
        package["x"] = GOOD_DOCK[0] + (queue_size % 2) * 32 - 16
        package["y"] = GOOD_DOCK[1] - (queue_size // 2) * 30
        package["z"] = GOOD_DOCK[2]
    else:
        rejected_packages += 1
        if package in packages:
            packages.remove(package)


def place_held_package():
    package = find_package(held_package_id)
    if package is None:
        return False

    tip_x, tip_y, tip_z = get_arm_tip()
    good_distance = distance_3d(tip_x, tip_y, tip_z,
                                GOOD_DOCK[0], GOOD_DOCK[1], GOOD_DOCK[2])
    bad_distance = distance_3d(tip_x, tip_y, tip_z,
                               BAD_BIN[0], BAD_BIN[1], BAD_BIN[2])


    if good_distance <= 55:
        finish_sorting(package, "good")
        return True
    if bad_distance <= 55:
        finish_sorting(package, "bad")
        return True

    set_message("Move the held package closer to the green or red bin")
    return False


def update_held_package_position():
    package = find_package(held_package_id)
    if package is not None:
        tip_x, tip_y, tip_z = get_arm_tip()
        package["x"] = tip_x
        package["y"] = tip_y
        package["z"] = tip_z - 15


def update_automatic_arm():
    global auto_arm_state, auto_package_id, arm_wait, gripper_open

    if not automatic_mode or emergency_stop or game_over:
        return

    if arm_wait > 0:
        arm_wait -= 1
        return

    if auto_arm_state == "home":
        set_arm_target(270, 50, 45, 0)
        if move_arm_to_target():
            package = nearest_waiting_package()
            if package is not None:
                auto_package_id = package["id"]
                gripper_open = True
                set_arm_target_to_point((package["x"],
                                         package["y"],
                                         package["z"] + 15))
                auto_arm_state = "moving_to_pickup"

    elif auto_arm_state == "moving_to_pickup":
        package = find_package(auto_package_id)
        if package is None or package["state"] != "waiting_arm":
            auto_arm_state = "returning"
            set_arm_target(270, 50, 45, 0)
        elif move_arm_to_target():
            gripper_open = False
            if pick_nearby_package():
                arm_wait = 18
                set_arm_target(base_angle, 57, 48, 0)
                auto_arm_state = "lifting"
            else:
                auto_arm_state = "returning"
                set_arm_target(270, 50, 45, 0)

    elif auto_arm_state == "lifting":
        if move_arm_to_target():
            package = find_package(held_package_id)
            if package is None:
                auto_arm_state = "returning"
                set_arm_target(270, 50, 45, 0)
            else:
                destination = BAD_BIN if package["defective"] else GOOD_DOCK
                set_arm_target_to_point(destination)
                auto_arm_state = "moving_to_drop"

    elif auto_arm_state == "moving_to_drop":
        if move_arm_to_target():
            arm_wait = 14
            auto_arm_state = "releasing"

    elif auto_arm_state == "releasing":
        package = find_package(held_package_id)
        if package is not None:
            selected_bin = "bad" if package["defective"] else "good"
            finish_sorting(package, selected_bin)
        gripper_open = True
        auto_package_id = None
        set_arm_target(270, 50, 45, 0)
        auto_arm_state = "returning"

    elif auto_arm_state == "returning":
        if move_arm_to_target():
            auto_arm_state = "home"


def spawn_package(force=False):
    global next_package_id, spawn_counter

    if not force:
        for package in packages:
            if (package["state"] == "conveyor" and
                    package["x"] < CONVEYOR_START_X + 60):
                return False

    package = {
        "id": next_package_id,
        "x": CONVEYOR_START_X,
        "y": CONVEYOR_Y,
        "z": PACKAGE_Z,
        "defective": random.random() < defect_chance,
        "inspected": False,
        "state": "conveyor"
    }
    packages.append(package)
    next_package_id += 1
    spawn_counter = 0
    return True


def inspect_package(package):
    global inspection_flash, last_inspection_defective, inspected_packages

    package["inspected"] = True
    inspection_flash = 35
    last_inspection_defective = package["defective"]
    inspected_packages += 1

    if package["defective"]:
        set_message("Scanner result: defective package detected")
    else:
        set_message("Scanner result: good package")


def update_conveyor():
    global spawn_counter, belt_offset, jam_pressure, jam_active

    if emergency_stop or game_over:
        return

    if not jam_active:
        current_line_packages = [package for package in packages
                                 if package["state"] == "conveyor"]


        if len(current_line_packages) < 5:
            spawn_counter += 1
            if spawn_counter >= 190:
                spawn_package()

        belt_offset = (belt_offset + 2) % 370

        moving_packages = [package for package in packages
                           if package["state"] == "conveyor"]
        moving_packages.sort(key=lambda package: package["x"], reverse=True)

        waiting_exists = any(package["state"] == "waiting_arm"
                             for package in packages)
        front_limit = CONVEYOR_END_X - 55 if waiting_exists else CONVEYOR_END_X

        for package in moving_packages:
            if package["x"] < front_limit:
                package["x"] = min(package["x"] + 1.25, front_limit)

            if (not package["inspected"] and
                    package["x"] >= INSPECTION_X):
                inspect_package(package)

            if (not waiting_exists and
                    package["x"] >= CONVEYOR_END_X):
                package["x"] = CONVEYOR_END_X
                package["state"] = "waiting_arm"
                waiting_exists = True

            front_limit = package["x"] - 52

        package_gaps = []
        for index in range(len(moving_packages) - 1):
            package_gaps.append(moving_packages[index]["x"] -
                                moving_packages[index + 1]["x"])


        unsafe_gap = bool(package_gaps) and min(package_gaps) < 42
        if len(moving_packages) >= 6 or unsafe_gap:
            jam_pressure += 1
        else:
            jam_pressure = max(0, jam_pressure - 2)


        if jam_pressure > 900:
            jam_active = True
            jam_pressure = 0
            set_message("Automatic jam detector stopped the conveyor", 300)


def update_safety_damage():
    global jam_damage_counter, factory_health

    if jam_active and not game_over:
        jam_damage_counter += 1
        if jam_damage_counter >= 300:
            factory_health = max(0, factory_health - 2)
            jam_damage_counter = 0
    else:
        jam_damage_counter = 0


def draw_agv():
    glPushMatrix()
    glTranslatef(agv_x, agv_y, 0)
    glRotatef(agv_angle, 0, 0, 1)

    body_color = ((0.86, 0.14, 0.10) if agv_blocked
                  else (0.12, 0.48, 0.82))
    draw_box(0, 0, 25, 82, 58, 30, body_color)
    draw_box(-3, 0, 47, 55, 45, 14, (0.18, 0.62, 0.88))

    for wheel_x in (-27, 27):
        for wheel_y in (-31, 31):
            glPushMatrix()
            glTranslatef(wheel_x, wheel_y, 15)
            glRotatef(90, 1, 0, 0)
            draw_cylinder(11, 7, (0.05, 0.05, 0.06))
            glPopMatrix()

    glPushMatrix()
    glTranslatef(40, 0, 39)
    draw_sphere(9, (0.95, 0.82, 0.12))
    glPopMatrix()


    if agv_cargo_type == "order":
        draw_box(0, 0, 68, 34, 30, 28, (0.94, 0.68, 0.12))

    glPopMatrix()


def draw_safety_barrier():
    if not barrier_active:
        return

    for offset in (-32, 32):
        glPushMatrix()
        glTranslatef(BARRIER_X, BARRIER_Y + offset, 0)
        draw_cylinder(8, 62, (0.86, 0.18, 0.12))
        glPopMatrix()
    draw_box(BARRIER_X, BARRIER_Y, 50, 12, 82, 10,
             (0.96, 0.72, 0.10))


def start_agv_route(job, route):
    global agv_job, agv_route, agv_route_index
    agv_job = job
    agv_route = route
    agv_route_index = 0


def ready_package_for_agv():
    ready_packages = [package for package in packages
                      if package["state"] == "ready_agv"]
    if not ready_packages:
        return None
    ready_packages.sort(key=lambda package: package["id"])
    return ready_packages[0]


def load_ready_package():
    global agv_cargo_type, agv_cargo_id

    package = ready_package_for_agv()
    if package is None:
        return False

    package["state"] = "agv"
    agv_cargo_type = "package"
    agv_cargo_id = package["id"]
    set_message("AGV loaded package " + str(package["id"]))
    return True


def update_agv_cargo_position():
    if agv_cargo_type == "package":
        package = find_package(agv_cargo_id)
        if package is not None:
            package["x"] = agv_x
            package["y"] = agv_y
            package["z"] = 66


def barrier_blocks_agv(target_x, target_y):
    if not barrier_active:
        return False

    current_distance = distance_2d(agv_x, agv_y,
                                   BARRIER_X, BARRIER_Y)
    to_target_x = target_x - agv_x
    to_target_y = target_y - agv_y
    to_barrier_x = BARRIER_X - agv_x
    to_barrier_y = BARRIER_Y - agv_y
    direction_dot = (to_target_x * to_barrier_x +
                     to_target_y * to_barrier_y)


    return current_distance < 92 and direction_dot > 0


def move_agv_to(target_x, target_y):
    global agv_x, agv_y, agv_angle, agv_blocked

    if barrier_blocks_agv(target_x, target_y):
        agv_blocked = True
        return False

    agv_blocked = False
    dx = target_x - agv_x
    dy = target_y - agv_y
    distance = math.sqrt(dx * dx + dy * dy)

    if distance <= 2.0:
        agv_x = target_x
        agv_y = target_y
        return True

    agv_angle = math.degrees(math.atan2(dy, dx))
    speed = 1.7
    agv_x += (dx / distance) * speed
    agv_y += (dy / distance) * speed
    return False


def finish_agv_job():
    global agv_job, agv_route, agv_cargo_type, agv_cargo_id
    global storage_inventory, stored_packages, score
    global pending_orders, orders_fulfilled, loading_flash

    if agv_job == "store":
        package = find_package(agv_cargo_id)
        if package is not None and package in packages:
            packages.remove(package)

        agv_cargo_type = None
        agv_cargo_id = None

        if storage_inventory < storage_capacity:
            storage_inventory += 1
            stored_packages += 1
            score += 6
            set_message("AGV stored a package in the warehouse")
        else:
            set_message("Warehouse is full - an order must leave first")

        if pending_orders > 0 and storage_inventory > 0:
            storage_inventory -= 1
            agv_cargo_type = "order"
            start_agv_route("deliver", [(420, 260), LOADING_DOCK])
        else:
            start_agv_route("return", [(250, 100), (50, 100), SORT_DOCK])

    elif agv_job == "fetch_order":
        if pending_orders > 0 and storage_inventory > 0:
            storage_inventory -= 1
            agv_cargo_type = "order"
            start_agv_route("deliver", [(420, 260), LOADING_DOCK])
        else:
            start_agv_route("return", [(250, 100), (50, 100), SORT_DOCK])

    elif agv_job == "deliver":
        if pending_orders > 0:
            pending_orders -= 1
        orders_fulfilled += 1
        score += 30
        loading_flash = 100
        agv_cargo_type = None
        set_message("Customer order delivered at the loading bay", 240)
        start_agv_route("return", [(420, 260), WAREHOUSE_DOCK,
                                   (250, 100), (50, 100), SORT_DOCK])

    elif agv_job == "return":
        agv_job = "idle"
        agv_route = []


def update_agv():
    global agv_route_index

    if emergency_stop or game_over:
        return

    if agv_job == "idle":
        if load_ready_package():
            start_agv_route("store", [(50, 100), (250, 100),
                                      WAREHOUSE_DOCK])
        elif pending_orders > 0 and storage_inventory > 0:
            start_agv_route("fetch_order", [(50, 100), (250, 100),
                                            WAREHOUSE_DOCK])
        return

    if agv_route_index >= len(agv_route):
        finish_agv_job()
        return

    target = agv_route[agv_route_index]
    if move_agv_to(target[0], target[1]):
        agv_route_index += 1
        if agv_route_index >= len(agv_route):
            finish_agv_job()

    update_agv_cargo_position()


def update_orders():
    global order_timer, pending_orders, order_wait_timer
    global missed_orders, factory_health

    if game_over:
        return

    order_timer += 1
    if order_timer >= 900:
        if pending_orders < 4:
            pending_orders += 1
            set_message("A new warehouse order has arrived")
        order_timer = 0

    if pending_orders > 0 and storage_inventory == 0:
        order_wait_timer += 1
        if order_wait_timer >= 1500:
            missed_orders += 1
            factory_health = max(0, factory_health - 5)
            order_wait_timer = 0
            set_message("Order delay reduced factory health")
    else:
        order_wait_timer = 0


def setupCamera():
    global camera_pos

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 3000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == 0:
        radian = math.radians(camera_angle)
        eye_x = camera_distance * math.cos(radian)
        eye_y = camera_distance * math.sin(radian)
        eye_z = camera_height
        camera_pos = (eye_x, eye_y, eye_z)
        gluLookAt(eye_x, eye_y, eye_z,
                  0, 0, 40,
                  0, 0, 1)

    elif camera_mode == 1:
        tip_x, tip_y, tip_z = get_arm_tip()
        camera_pos = (-520, -260, 280)
        gluLookAt(-520, -260, 280,
                  tip_x, tip_y, tip_z,
                  0, 0, 1)

    else:
        angle_radian = math.radians(agv_angle)
        eye_x = agv_x - 150 * math.cos(angle_radian)
        eye_y = agv_y - 150 * math.sin(angle_radian)
        eye_z = 120
        camera_pos = (eye_x, eye_y, eye_z)
        gluLookAt(eye_x, eye_y, eye_z,
                  agv_x, agv_y, 28,
                  0, 0, 1)


def camera_name():
    if camera_mode == 0:
        return "Overview"
    if camera_mode == 1:
        return "Robotic Arm"
    return "AGV Follow"


def draw_hud():
    draw_text(20, 770, "FACTORYFLOW 3D | SMART FACTORY SIMULATOR")

    if not difficulty_selected:
        draw_text(470, 470, "SELECT DIFFICULTY")
        draw_text(430, 425, "Press 1 - EASY: 240 seconds, 5 orders, 18% defects")
        draw_text(410, 390, "Press 2 - NORMAL: 180 seconds, 6 orders, 30% defects")
        draw_text(420, 355, "Press 3 - HARD: 140 seconds, 7 orders, 42% defects")
        draw_text(455, 310, "Press M after starting to play manually")
        return

    mode_text = "AUTO" if automatic_mode else "MANUAL"
    state_text = "RUNNING"
    if emergency_stop:
        state_text = "EMERGENCY STOP"
    elif jam_active:
        state_text = "CONVEYOR JAM"
    elif agv_blocked:
        state_text = "AGV OBSTACLE"

    draw_text(20, 742,
              "Difficulty: " + difficulty_level +
              "   Score: " + str(score) +
              "   Health: " + str(factory_health) + "%" +
              "   Shift: " + str(shift_seconds) + "s" +
              "   State: " + state_text)
    draw_text(20, 714,
              "Arm: " + mode_text +
              "   Camera: " + camera_name() +
              "   Sorted: " + str(sorted_packages) +
              "   Rejected: " + str(rejected_packages))
    draw_text(20, 686,
              "Inventory: " + str(storage_inventory) + "/" +
              str(storage_capacity) +
              "   Pending Orders: " + str(pending_orders) +
              "   Delivered: " + str(orders_fulfilled) + "/" +
              str(ORDER_TARGET))

    if status_timer > 0:
        draw_text(20, 652, "STATUS: " + status_message,
                  GLUT_BITMAP_HELVETICA_12)

    draw_text(20, 48,
              "ARM: A/D base | W/S shoulder | Q/E elbow | Z/X wrist | "
              "G gripper | M auto/manual",
              GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 26,
              "FACTORY: 1/2/3 difficulty | SPACE emergency | J jam | B obstacle | "
              "O order | C/right-click camera | Arrows view | R restart",
              GLUT_BITMAP_HELVETICA_12)

    if game_over:
        result = "SHIFT COMPLETED - TARGET ACHIEVED" if game_won else "SHIFT FAILED"
        draw_text(420, 430, result)
        draw_text(455, 395,
                  "Final Score: " + str(score) +
                  " | Orders: " + str(orders_fulfilled))
        draw_text(505, 360, "Press R to restart the factory")


def draw_complete_factory():
    draw_factory_floor()
    draw_factory_walls()

    draw_control_room()
    draw_maintenance_room()
    draw_loading_bay()

    draw_conveyor()
    draw_inspection_scanner()
    draw_sorting_bins()
    draw_robot_arm()

    draw_warehouse_racks()
    draw_safety_barrier()
    draw_agv()
    draw_packages()


def check_game_state():
    global game_over, game_won, score

    if game_over:
        return

    if orders_fulfilled >= ORDER_TARGET:
        game_over = True
        game_won = True
        score += 100
        set_message("Production target completed", 600)
    elif factory_health <= 0 or shift_seconds <= 0:
        game_over = True
        game_won = False
        set_message("The shift ended before the target was completed", 600)


def update_factory():
    global simulation_frame, clock_counter, shift_seconds
    global inspection_flash, loading_flash, status_timer

    simulation_frame += 1

    if status_timer > 0:
        status_timer -= 1
    if inspection_flash > 0:
        inspection_flash -= 1
    if loading_flash > 0:
        loading_flash -= 1

    if not difficulty_selected or game_over:
        return

    clock_counter += 1
    if clock_counter >= 60:
        shift_seconds = max(0, shift_seconds - 1)
        clock_counter = 0

    update_conveyor()
    update_automatic_arm()
    update_held_package_position()
    update_agv()
    update_orders()
    update_safety_damage()
    check_game_state()


def reset_game():
    global base_angle, shoulder_angle, elbow_angle, wrist_angle
    global gripper_open, automatic_mode, held_package_id
    global auto_arm_state, auto_package_id, arm_wait
    global target_base_angle, target_shoulder_angle
    global target_elbow_angle, target_wrist_angle
    global packages, next_package_id, spawn_counter, belt_offset
    global inspection_flash, last_inspection_defective
    global inspected_packages, sorted_packages, rejected_packages
    global escaped_defects, jam_active, jam_pressure
    global jam_damage_counter, emergency_stop
    global agv_x, agv_y, agv_angle, agv_job, agv_route
    global agv_route_index, agv_cargo_type, agv_cargo_id, agv_blocked
    global barrier_active, storage_inventory, stored_packages
    global pending_orders, orders_fulfilled, missed_orders
    global order_timer, order_wait_timer, loading_flash
    global score, factory_health, shift_seconds, clock_counter
    global simulation_frame, game_over, game_won

    base_angle = 270
    shoulder_angle = 50
    elbow_angle = 45
    wrist_angle = 0
    gripper_open = True
    automatic_mode = True
    held_package_id = None

    auto_arm_state = "home"
    auto_package_id = None
    arm_wait = 0
    target_base_angle = 270
    target_shoulder_angle = 50
    target_elbow_angle = 45
    target_wrist_angle = 0

    packages = []
    next_package_id = 1
    spawn_counter = 120
    belt_offset = 0

    inspection_flash = 0
    last_inspection_defective = False
    inspected_packages = 0
    sorted_packages = 0
    rejected_packages = 0
    escaped_defects = 0
    jam_active = False
    jam_pressure = 0
    jam_damage_counter = 0
    emergency_stop = False

    agv_x = SORT_DOCK[0]
    agv_y = SORT_DOCK[1]
    agv_angle = 0
    agv_job = "idle"
    agv_route = []
    agv_route_index = 0
    agv_cargo_type = None
    agv_cargo_id = None
    agv_blocked = False
    barrier_active = False

    storage_inventory = 0
    stored_packages = 0
    pending_orders = 1
    orders_fulfilled = 0
    missed_orders = 0
    order_timer = 0
    order_wait_timer = 0
    loading_flash = 0

    score = 0
    factory_health = 100
    shift_seconds = SHIFT_LIMIT
    clock_counter = 0
    simulation_frame = 0
    game_over = False
    game_won = False

    spawn_package(True)
    if packages:
        packages[0]["x"] = -540

    set_message("New shift started - automatic production is active", 240)


def select_difficulty(level):
    global difficulty_level, difficulty_selected
    global SHIFT_LIMIT, ORDER_TARGET, defect_chance

    if level == "EASY":
        difficulty_level = "EASY"
        SHIFT_LIMIT = 240
        ORDER_TARGET = 5
        defect_chance = 0.18
    elif level == "HARD":
        difficulty_level = "HARD"
        SHIFT_LIMIT = 140
        ORDER_TARGET = 7
        defect_chance = 0.42
    else:
        difficulty_level = "NORMAL"
        SHIFT_LIMIT = 180
        ORDER_TARGET = 6
        defect_chance = 0.30

    difficulty_selected = True
    reset_game()
    set_message(difficulty_level + " difficulty started", 240)


def keyboardListener(key, x, y):
    global base_angle, shoulder_angle, elbow_angle, wrist_angle
    global gripper_open, automatic_mode, auto_arm_state
    global emergency_stop, jam_active, barrier_active
    global pending_orders, camera_mode

    try:
        pressed_key = key.decode("utf-8").lower()
    except AttributeError:
        pressed_key = str(key).lower()

    if pressed_key == "1":
        select_difficulty("EASY")
        glutPostRedisplay()
        return
    elif pressed_key == "2":
        select_difficulty("NORMAL")
        glutPostRedisplay()
        return
    elif pressed_key == "3":
        select_difficulty("HARD")
        glutPostRedisplay()
        return

    if not difficulty_selected:
        glutPostRedisplay()
        return

    if pressed_key == "r":
        reset_game()
        glutPostRedisplay()
        return

    if pressed_key == "c":
        camera_mode = (camera_mode + 1) % 3
        set_message("Camera changed to " + camera_name())

    if game_over:
        glutPostRedisplay()
        return


    if not automatic_mode:
        if pressed_key == "a":
            base_angle = (base_angle + 5) % 360
        elif pressed_key == "d":
            base_angle = (base_angle - 5) % 360
        elif pressed_key == "w":
            shoulder_angle = min(60, shoulder_angle + 5)
        elif pressed_key == "s":
            shoulder_angle = max(-30, shoulder_angle - 5)
        elif pressed_key == "q":
            elbow_angle = min(90, elbow_angle + 5)
        elif pressed_key == "e":
            elbow_angle = max(0, elbow_angle - 5)
        elif pressed_key == "z":
            wrist_angle = min(90, wrist_angle + 5)
        elif pressed_key == "x":
            wrist_angle = max(-90, wrist_angle - 5)

    if pressed_key == "m":
        automatic_mode = not automatic_mode
        auto_arm_state = "home"
        if automatic_mode:
            set_message("Automatic robotic-arm mode enabled")
        else:
            set_message("Manual robotic-arm mode enabled")

    elif pressed_key == "g" and not automatic_mode:
        if gripper_open:
            gripper_open = False
            pick_nearby_package()
        elif held_package_id is not None:
            if place_held_package():
                gripper_open = True
        else:
            gripper_open = True
            set_message("Gripper opened")

    elif pressed_key == " ":
        emergency_stop = not emergency_stop
        if emergency_stop:
            set_message("Emergency stop activated - all machines are frozen", 300)
        else:
            set_message("Emergency stop released - production resumed", 240)

    elif pressed_key == "j":
        jam_active = not jam_active
        if jam_active:
            set_message("Manual jam test activated", 240)
        else:
            set_message("Conveyor jam cleared by maintenance", 240)

    elif pressed_key == "b":
        barrier_active = not barrier_active
        if barrier_active:
            set_message("Safety obstacle placed in the AGV corridor")
        else:
            set_message("Safety obstacle removed from the AGV corridor")

    elif pressed_key == "o":
        pending_orders = min(4, pending_orders + 1)
        set_message("Manual customer order added")

    glutPostRedisplay()


def specialKeyListener(key, x, y):
    global camera_angle, camera_height

    if key == GLUT_KEY_UP:
        camera_height = min(1200, camera_height + 20)
    elif key == GLUT_KEY_DOWN:
        camera_height = max(220, camera_height - 20)
    elif key == GLUT_KEY_LEFT:
        camera_angle = (camera_angle + 3) % 360
    elif key == GLUT_KEY_RIGHT:
        camera_angle = (camera_angle - 3) % 360

    glutPostRedisplay()


def mouseListener(button, state, x, y):
    global camera_mode

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = (camera_mode + 1) % 3
        set_message("Camera changed to " + camera_name())
        glutPostRedisplay()


def idle():
    update_factory()
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    setupCamera()
    draw_complete_factory()
    draw_hud()

    glutSwapBuffers()


def print_controls():
    print("\nFactoryFlow 3D Controls")
    print("1: Easy              2: Normal             3: Hard")
    print("A/D: Base rotation     W/S: Shoulder")
    print("Q/E: Elbow            Z/X: Wrist")
    print("G: Gripper            M: Auto/Manual arm")
    print("SPACE: Emergency stop J: Conveyor jam test")
    print("B: AGV obstacle       O: Add order")
    print("C/Right click: Camera Arrow keys: Camera movement")
    print("R: Restart\n")


def main():
    global quadric

    glutInit()
    glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"FactoryFlow 3D - Smart Factory Simulator")

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.05, 0.07, 0.09, 1.0)
    quadric = gluNewQuadric()

    reset_game()
    print_controls()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()
