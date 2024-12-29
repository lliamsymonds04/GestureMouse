import math
import mouse
import pyautogui

#SENSIVITY VARS
SENSITIVITY_X = 1.5
SENSITIVITY_Y = 1.5
JUMP_SPEED_THRESHOLD = 0.25
JUMP_MULTIPLIER = 2

#CLICKS
CLICK_VELOCITY = 0.1
CLICK_DEBOUNCE = 0.1

from PointTracker import PointTracker
from Debounce import Debounce

def calculate_magnitude(v: (float, float)) -> float:
    return math.sqrt(pow(v[0], 2) + pow(v[1], 2))

def log_curve(x: float, a: float):
    return math.copysign(math.log(abs(x) + 1) + 1, x) * a

class MouseController:
    def __init__(self):
        self.left_click_debounce = Debounce(CLICK_DEBOUNCE)
        self.right_click_debounce = Debounce(CLICK_DEBOUNCE)

    def update(self, trackers: dict[str, PointTracker], dt: float):
        wrist_tracker = trackers["wrist"]
        displacement_magnitude = calculate_magnitude(wrist_tracker.displacement)

        if displacement_magnitude > 0.001:
            screen_width, screen_height = pyautogui.size()

            vel = tuple(d/dt for d in wrist_tracker.displacement)
            speed = calculate_magnitude(vel)

            sens_scale = 1
            if speed > JUMP_SPEED_THRESHOLD:
                sens_scale *= JUMP_MULTIPLIER

            x = int(wrist_tracker.displacement[0] * screen_width * SENSITIVITY_X * sens_scale)
            y = int(wrist_tracker.displacement[1] * screen_height * SENSITIVITY_Y * sens_scale)
            mouse.move(x, y, False)
        else: #stationary
            if self.left_click_debounce:
                index_finger_tracker = trackers["index finger"]
                y_vel = index_finger_tracker.displacement[1]/dt

                if y_vel > CLICK_VELOCITY:
                    self.left_click_debounce.activate()
                    mouse.click()

            if self.right_click_debounce:
                right_finger_tracker = trackers["index finger"]
                y_vel = right_finger_tracker.displacement[1] / dt

                if y_vel > CLICK_VELOCITY:
                    self.right_click_debounce.activate()
                    mouse.right_click()