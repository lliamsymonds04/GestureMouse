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
JUMP_MULTIPLIER = 2.5

#CLICKS
CLICK_VELOCITY = 0.15
CLICK_DEBOUNCE = 0.15
SIDE_BUTTON_DEBOUNCE = 0.5
BACK_BUTTON_VELOCITY_THRESHOLD = 0.25
PINKY_PINCH_THRESHOLD = 0.02
INDEX_PINCH_THRESHOLD = 0.015
PINKY_PINCH_DEBOUNCE = 1
INDEX_PINCH_DEBOUNCE = 0.2

#scrolling
SCROLL_FACTOR = 50
SCROLL_VELOCITY_THRESHOLD = 0.25

finger_names = ["index", "middle", "ring", "pinky"]
left_right = ["left", "right"]

mouse2 = Controller() # I need this to access the side buttons

def calculate_magnitude(v: (float, float)) -> float:
    return math.sqrt(pow(v[0], 2) + pow(v[1], 2))

init_time = time.time()

class MouseController:
    def __init__(self, debug_mode: bool):
        self.click_debounce = Debounce(CLICK_DEBOUNCE)
        self.side_button_debounce = Debounce(SIDE_BUTTON_DEBOUNCE)
        self.pinky_pinch_debounce = Debounce(PINKY_PINCH_DEBOUNCE)
        self.index_pinch_debounce = Debounce(INDEX_PINCH_DEBOUNCE)
        self.state = "open"
        self.active = False
        self.dragging = False
        self.debug_mode = debug_mode
        self.can_left_click = True
        self.can_right_click = True

    def output_message(self, msg: str):
        if self.debug_mode:
            print(msg)

    def get_can_click(self, side: str):
        if side == "left":
            return self.can_left_click
        elif side == "right":
            return self.can_right_click

    def set_can_click(self, side: str, v: bool):
        if side == "left":
            self.can_left_click = v
        elif side == "right":
            self.can_right_click = v

    def update(self, trackers: dict[str, PointTracker], dt: float):
        thumb = trackers["thumb"]

        if self.active:
            wrist_tracker = trackers["wrist"]
            displacement_magnitude = calculate_magnitude(wrist_tracker.displacement)
            wrist_velocity = displacement_magnitude/dt

            fingers_down = [0,0,0,0]
            fingers_down_sum = 0
            moving_fingers = 0
            for i, finger_name in enumerate(finger_names):
                finger_tracker = trackers[f"{finger_name} finger"]
                knuckle_tracker = trackers[f"{finger_name} knuckle"]

                y_vel = (finger_tracker.displacement[1] - wrist_tracker.displacement[1]) / dt


                if finger_tracker.y > knuckle_tracker.y:
                    fingers_down[i] = 1
                    fingers_down_sum += 1

                if abs(y_vel) > CLICK_VELOCITY * 0.3:
                    moving_fingers += 1



            # if fingers_down[0] == 1 and fingers_down[1] == 1 and fingers_down[2] == 1 and fingers_down[3] == 1:
            if self.state == "closed" and wrist_velocity > 0.05:
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

            #dragging
            index_finger = trackers["index finger"]
            index_to_thumb_distance = calculate_magnitude((index_finger.x - thumb.x, index_finger.y - thumb.y))

            if self.index_pinch_debounce:
                if self.dragging:
                    if index_to_thumb_distance > INDEX_PINCH_THRESHOLD * 4 or self.state == "closed":
                        self.index_pinch_debounce.activate()

                        self.dragging = False
                        mouse.release(button='left')
                        self.output_message("released")
                else:
                    if index_to_thumb_distance < INDEX_PINCH_THRESHOLD:
                        self.index_pinch_debounce.activate()

                        self.dragging = True
                        mouse.press(button='left')
                        self.output_message("pinch")


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
                # if moving_fingers >=2 :
                #     print("fingers moving")
                if self.state == "open"  and not self.dragging: #and moving_fingers < 2
                    # `if self.click_debounce:
                    #     y_vel = index_finger.displacement[1]/dt
                    #    thumb_vel = calculate_magnitude(thumb.displacement)/dt
                    #
                    #     if y_vel > CLICK_VELOCITY and thumb_vel < CLICK_VELOCITY * 0.5:
                    #         self.output_message("left click " + str(time.time() - init_time))
                    #
                    #         self.click_debounce.activate()
                    #         mouse.click()
                    # index_y_vel = index_finger.displacement[1]/dt
                    #

                    # for side in left_right:
                    fingers = ["index", "middle"]
                    thumb_vel = calculate_magnitude(thumb.displacement)/dt

                    for i in range(2):
                        click = left_right[i]
                        tracker = trackers[f"{fingers[i]} finger"]

                        finger_y_vel = tracker.displacement[1]/dt


                        if self.get_can_click(click):
                            if finger_y_vel > CLICK_VELOCITY and thumb_vel < CLICK_VELOCITY * 0.5:
                                self.output_message(f"{click} click " + str(time.time() - init_time))

                                mouse.click(button=click)
                                self.set_can_click(click, False)
                        else:
                            if finger_y_vel < 0:
                                self.set_can_click(click, True)
                                self.output_message(f"{click }click reset")


                    # if self.click_debounce:
                    #     right_finger = trackers["middle finger"]
                    #     y_vel = right_finger.displacement[1] / dt
                    #
                    #     if y_vel > CLICK_VELOCITY:
                    #         self.output_message("right click " + str(time.time() - init_time))
                    #
                    #         self.click_debounce.activate()
                    #         mouse.right_click()


        thumb = trackers["thumb"]
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