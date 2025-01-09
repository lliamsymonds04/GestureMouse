import math
import mouse
import pyautogui
from pynput.mouse import Button, Controller
import time

from PointTracker import PointTracker
from Debounce import Debounce

#SENSIVITY VARS
SENSITIVITY_X = 1.75
SENSITIVITY_Y = 1.75
JUMP_SPEED_THRESHOLD = 0.2
JUMP_MULTIPLIER = 3

#CLICKS
CLICK_VELOCITY = 0.15
CLICK_DEBOUNCE = 0.15
SIDE_BUTTON_DEBOUNCE = 0.5
BACK_BUTTON_VELOCITY_THRESHOLD = 0.25
PINKY_PINCH_THRESHOLD = 0.02
CLICK_PINCH_THRESHOLD = 0.03
PINKY_PINCH_DEBOUNCE = 1
INDEX_PINCH_DEBOUNCE = 0.2

#scrolling
SCROLL_FACTOR = 50
SCROLL_VELOCITY_THRESHOLD = 0.25

STATIONARY_DISPLACEMENT = 0.001

finger_names = ["index", "middle", "ring", "pinky"]
left_right = ["left", "right"]

mouse2 = Controller() # I need this to access the side buttons

def calculate_magnitude(v: (float, float)) -> float:
    return math.sqrt(pow(v[0], 2) + pow(v[1], 2))

init_time = time.time()

class MouseController:
    def __init__(self, debug_mode: bool):
        self.debug_mode = debug_mode
        self.state = "open"
        self.active = False
        self.is_left_click_held = False
        self.is_right_click_held = False

        self.click_debounce = Debounce(CLICK_DEBOUNCE)
        self.side_button_debounce = Debounce(SIDE_BUTTON_DEBOUNCE)
        self.pinky_pinch_debounce = Debounce(PINKY_PINCH_DEBOUNCE)
        self.index_pinch_debounce = Debounce(INDEX_PINCH_DEBOUNCE)

    def output_message(self, msg: str):
        if self.debug_mode:
            print(msg)

    def get_mouse_button_down(self, click: str):
        if click == "left":
            return self.is_left_click_held
        elif click == "right":
            return self.is_right_click_held

    def set_mouse_button_down(self, click: str, is_down: bool):
        if click == "left":
            self.is_left_click_held = is_down
        if click == "right":
            self.is_right_click_held = is_down

    def update(self, trackers: dict[str, PointTracker], dt: float):
        thumb = trackers["thumb"]

        if self.active:
            wrist_tracker = trackers["wrist"]
            displacement_magnitude = calculate_magnitude(wrist_tracker.displacement)
            wrist_velocity = displacement_magnitude/dt

            fingers_down = [0,0,0,0]
            fingers_down_sum = 0
            for i, finger_name in enumerate(finger_names):
                finger_tracker = trackers[f"{finger_name} finger"]
                knuckle_tracker = trackers[f"{finger_name} knuckle"]

                if finger_tracker.y > knuckle_tracker.y:
                    fingers_down[i] = 1
                    fingers_down_sum += 1


            # if fingers_down[0] == 1 and fingers_down[1] == 1 and fingers_down[2] == 1 and fingers_down[3] == 1:
            if self.state == "closed" and wrist_velocity > 0.01:
                # new_state = "closed"
                pass
            if fingers_down_sum > 3:
                new_state = "closed"
            elif fingers_down[0] == 0 and fingers_down[1] == 0 and fingers_down[2] == 1 and fingers_down[3] == 1:
                new_state = "two up"
            # elif fingers_down[0] == 0 and fingers_down[1] == 0 and fingers_down[2] == 0 and fingers_down[3] == 0:
            elif fingers_down_sum == 0:
                new_state = "open"
            else:
                new_state = "transitioning"

            if self.debug_mode and new_state != self.state:
                print(new_state, time.time()-init_time)

            self.state = new_state

            if displacement_magnitude > STATIONARY_DISPLACEMENT:
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


            # else: #stationary
            if self.state == "open":
                fingers = ["index", "middle"]

                # if self.click_debounce:
                for i in range(2):
                    button = left_right[i]
                    tracker = trackers[f"{fingers[i]} finger"]

                    distance_to_thumb = calculate_magnitude((tracker.x - thumb.x, tracker.y - thumb.y))
                    is_button_down = self.get_mouse_button_down(button)

                    if distance_to_thumb < CLICK_PINCH_THRESHOLD and not is_button_down and self.click_debounce:
                        mouse.press(button=button)
                        self.click_debounce.activate()
                        self.set_mouse_button_down(button, True)
                        self.output_message(f"{button} button pressed: {time.time() - init_time}")

                    if distance_to_thumb > CLICK_PINCH_THRESHOLD * 1.3 and is_button_down and displacement_magnitude <= STATIONARY_DISPLACEMENT:
                        mouse.release(button=button)
                        self.click_debounce.activate()

                        self.set_mouse_button_down(button, False)
                        self.output_message(f"{button} button released: {time.time() - init_time}")


        pinky = trackers["pinky finger"]

        d_x = thumb.x - pinky.x
        d_y = thumb.y - pinky.y

        pinky_distance = calculate_magnitude((d_x, d_y))
        if pinky_distance < PINKY_PINCH_THRESHOLD and self.pinky_pinch_debounce:
            self.pinky_pinch_debounce.activate()

            self.active = not self.active

            if self.active:
                print("Activated the mouse")
            else:
                print("Deactivated the mouse")