import time
import keyboard
import cv2

from HandTracker import HandTracker
from MouseController import MouseController

if __name__ == "__main__":
    pass

    hand_tracker = HandTracker(model_path='Models\\hand_landmarker.task', debug_mode=False)
    mouse_controller = MouseController()

    prev_time = time.time()
    while True:
        now = time.time()
        dt = max(now - prev_time, 1/100)

        hand_tracker.update(dt)
        mouse_controller.update(hand_tracker.trackers, dt)

        prev_time = now

        if (cv2.waitKey(1) & 0xFF == 27) or keyboard.is_pressed('esc'): #esc key
            print("exiting...")
            hand_tracker.close()
            break