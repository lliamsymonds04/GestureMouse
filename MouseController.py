import math
import mouse
import pyautogui
from pynput.mouse import Button, Controller

from PointTracker import PointTracker
from Debounce import Debounce

#SENSIVITY VARS
SENSITIVITY_X = 1.5
SENSITIVITY_Y = 1.5
JUMP_SPEED_THRESHOLD = 0.2
JUMP_MULTIPLIER = 2.5

#CLICKS
CLICK_VELOCITY = 0.15
CLICK_DEBOUNCE = 0.15
SIDE_BUTTON_DEBOUNCE = 0.5
BACK_BUTTON_VELOCITY_THRESHOLD = 0.25
PINCH_THRESHOLD = 0.02
PINKY_PINCH_DEBOUNCE = 1
INDEX_PINCH_DEBOUNCE = 0.2

#scrolling
SCROLL_FACTOR = 50
SCROLL_VELOCITY_THRESHOLD = 0.25

finger_names = ["index", "middle", "ring", "pinky"]

mouse2 = Controller() # I need this to access the side buttons

def calculate_magnitude(v: (float, float)) -> float:
    return math.sqrt(pow(v[0], 2) + pow(v[1], 2))

class MouseController:
    def __init__(self):
        self.click_debounce = Debounce(CLICK_DEBOUNCE)
        self.side_button_debounce = Debounce(SIDE_BUTTON_DEBOUNCE)
        self.pinky_pinch_debounce = Debounce(PINKY_PINCH_DEBOUNCE)
        self.index_pinch_debounce = Debounce(INDEX_PINCH_DEBOUNCE)
        self.state = "open"
        self.active = False
        self.dragging = False

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


            #dragging
            index_finger = trackers["index finger"]
            thumb = trackers["thumb"]
            index_to_thumb_distance = calculate_magnitude((index_finger.x - thumb.x, index_finger.y - thumb.y))

            if self.index_pinch_debounce:
                if self.dragging:
                    if index_to_thumb_distance > PINCH_THRESHOLD * 3 or self.state == "closed":
                        self.index_pinch_debounce.activate()

                        self.dragging = False
                        mouse.release(button='left')
                else:
                    if index_to_thumb_distance < PINCH_THRESHOLD:
                        self.index_pinch_debounce.activate()

                        self.dragging = True
                        mouse.press(button='left')


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
                    if self.click_debounce:
                        y_vel = index_finger.displacement[1]/dt

                        if y_vel > CLICK_VELOCITY:
                            # print("left click", time.time() - init_time)

                            self.click_debounce.activate()
                            mouse.click()

                    if self.click_debounce:
                        right_finger = trackers["middle finger"]
                        y_vel = right_finger.displacement[1] / dt

                        if y_vel > CLICK_VELOCITY:
                            # print("right click", time.time() - init_time)

                            self.click_debounce.activate()
                            mouse.right_click()


        thumb = trackers["thumb"]
        pinky = trackers["pinky finger"]

        d_x = thumb.x - pinky.x
        d_y = thumb.y - pinky.y

        pinky_distance = calculate_magnitude((d_x, d_y))
        if pinky_distance < PINCH_THRESHOLD and self.pinky_pinch_debounce:
            self.pinky_pinch_debounce.activate()

            self.active = not self.active

            if self.active:
                print("Activated the mouse")
            else:
                print("Deactivated the mouse")