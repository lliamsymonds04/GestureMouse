import math
import time
import mouse
import pyautogui

VELOCITY_SCALAR_X = 0.05
VELOCITY_SCALAR_Y = 0.1
MIN_MOVEMENT_THRESHOLD = 0.05

JUMP_THRESHOLD = 0.5
JUMP_MULTIPLIER = 2

from Spring import Spring
from PointTracker import PointTracker

def calculate_magnitude(v: (float, float)) -> float:
    return math.sqrt(pow(v[0], 2) + pow(v[1], 2))

def log_curve(x: float, a: float):
    return math.copysign(math.log(abs(x) + 1) + 1, x) * a

class MouseController:
    def __init__(self):
        pass

    def update(self, index_finger_tracker: PointTracker, dt: float):
        displacement_magnitude = calculate_magnitude(index_finger_tracker.displacement)

        if displacement_magnitude > 0.001:
            screen_width, screen_height = pyautogui.size()

            x = int(index_finger_tracker.displacement[0] * screen_width)
            y = int(index_finger_tracker.displacement[1] * screen_height)
            mouse.move(x, y, False)