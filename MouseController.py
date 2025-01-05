import math
import mouse
import pyautogui
from pynput.mouse import Button, Controller

#SENSIVITY VARS
SENSITIVITY_X = 1.5
SENSITIVITY_Y = 1.5
JUMP_SPEED_THRESHOLD = 0.25
JUMP_MULTIPLIER = 2

#CLICKS
CLICK_VELOCITY = 0.1
CLICK_DEBOUNCE = 0.15
SIDE_BUTTON_DEBOUNCE = 0.5
BACK_BUTTON_VELOCITY_THRESHOLD = 0.25

#scrolling
SCROLL_FACTOR = 50
SCROLL_VELOCITY_THRESHOLD = 0.25

from PointTracker import PointTracker
from Debounce import Debounce

def calculate_magnitude(v: (float, float)) -> float:
    return math.sqrt(pow(v[0], 2) + pow(v[1], 2))

def log_curve(x: float, a: float):
    return math.copysign(math.log(abs(x) + 1) + 1, x) * a

finger_names = ["index", "middle", "ring", "pinky"]

mouse2 = Controller()

class MouseController:
    def __init__(self):
        self.left_click_debounce = Debounce(CLICK_DEBOUNCE)
        self.right_click_debounce = Debounce(CLICK_DEBOUNCE)
        self.side_button_debounce = Debounce(SIDE_BUTTON_DEBOUNCE)
        self.pinky_pinch_debounce = Debounce(1)
        self.state = "open"
        self.active = False

    def update(self, trackers: dict[str, PointTracker], dt: float):
        if self.active:
            wrist_tracker = trackers["wrist"]
            displacement_magnitude = calculate_magnitude(wrist_tracker.displacement)

            fingers_down = [0,0,0,0]
            moving_fingers = 0
            for i, finger_name in enumerate(finger_names):
                finger_tracker = trackers[f"{finger_name} finger"]
                knuckle_tracker = trackers[f"{finger_name} knuckle"]

                y_vel = (finger_tracker.displacement[1] - wrist_tracker.displacement[1]) / dt
                if abs(y_vel) > CLICK_VELOCITY:
                    moving_fingers += 1
                    break

                if finger_tracker.y > knuckle_tracker.y:
                    fingers_down[i] = 1

            if fingers_down[0] == 1 and fingers_down[1] == 1 and fingers_down[2] == 1 and fingers_down[3] == 1:
                self.state = "closed"
            elif fingers_down[0] == 0 and fingers_down[1] == 0 and fingers_down[2] == 1 and fingers_down[3] == 1:
                self.state = "two up"
            elif fingers_down[0] == 0 and fingers_down[1] == 0 and fingers_down[2] == 0 and fingers_down[3] == 0:
                self.state = "open"
            else:
                self.state = "transitioning"

            if displacement_magnitude > 0.001:
                if self.state == "open":
                    screen_width, screen_height = pyautogui.size()

                    vel = tuple(d/dt for d in wrist_tracker.displacement)
                    speed = calculate_magnitude(vel)

                    sens_scale = 1
                    if speed > JUMP_SPEED_THRESHOLD:
                        sens_scale *= JUMP_MULTIPLIER

                    x = int(wrist_tracker.displacement[0] * screen_width * SENSITIVITY_X * sens_scale)
                    y = int(wrist_tracker.displacement[1] * screen_height * SENSITIVITY_Y * sens_scale)
                    mouse.move(x, y, False)
                elif self.state == "two up":
                    x_vel = wrist_tracker.displacement[0]/dt

                    if x_vel < - BACK_BUTTON_VELOCITY_THRESHOLD and self.side_button_debounce:
                        self.side_button_debounce.activate()
                        mouse2.press(Button.x1)
                        mouse2.release(Button.x1)
                    elif x_vel > BACK_BUTTON_VELOCITY_THRESHOLD and self.side_button_debounce:
                        self.side_button_debounce.activate()
                        mouse2.press(Button.x2)
                        mouse2.release(Button.x2)
                elif self.state == "closed":
                    if wrist_tracker.displacement[1]/dt > SCROLL_VELOCITY_THRESHOLD:
                        mouse.wheel(1)
                    elif wrist_tracker.displacement[1]/dt < -SCROLL_VELOCITY_THRESHOLD:
                        mouse.wheel(-1)


            else: #stationary
                if self.state == "open" and moving_fingers < 2:
                    if self.left_click_debounce:
                        index_finger_tracker = trackers["index finger"]
                        y_vel = index_finger_tracker.displacement[1]/dt

                        if y_vel > CLICK_VELOCITY:
                            self.left_click_debounce.activate()
                            mouse.click()

                    if self.right_click_debounce:
                        right_finger_tracker = trackers["middle finger"]
                        y_vel = right_finger_tracker.displacement[1] / dt

                        if y_vel > CLICK_VELOCITY:
                            self.right_click_debounce.activate()
                            mouse.right_click()


        thumb = trackers["thumb"]
        pinky = trackers["pinky finger"]

        d_x = thumb.x - pinky.x
        d_y = thumb.y - pinky.y

        pinky_distance = calculate_magnitude((d_x, d_y))
        if pinky_distance < 0.02 and self.pinky_pinch_debounce:
            self.pinky_pinch_debounce.activate()

            self.active = not self.active