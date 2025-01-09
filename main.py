import time
import keyboard
import cv2

from HandTracker import HandTracker
from MouseController import MouseController
import DebugCamera

DEBUG_MODE = True

if __name__ == "__main__":
    pass

    hand_tracker = HandTracker(model_path='Models\\hand_landmarker.task', debug_mode=DEBUG_MODE)
    mouse_controller = MouseController(DEBUG_MODE)

    if DEBUG_MODE:
        DebugCamera.init()

    prev_time = time.time()
    while True:
        now = time.time()
        dt = max(now - prev_time, 1/100)

        img = hand_tracker.update()

        if hand_tracker.can_see_hand:
            mouse_controller.update(hand_tracker.trackers, dt)

        prev_time = now

        if DEBUG_MODE:
            DebugCamera.update(img, mouse_controller.state)

        if (cv2.waitKey(1) & 0xFF == 27) or keyboard.is_pressed('esc'): #esc key
            print("exiting...")
            hand_tracker.close()
            break