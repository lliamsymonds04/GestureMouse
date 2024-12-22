import time
import keyboard

from HandTracker import HandTracker
from MouseController import MouseController

if __name__ == "__main__":
    pass

    hand_tracker = HandTracker(model_path='Models\\hand_landmarker.task')
    mouse_controller = MouseController()

    prev_time = time.time()
    while True:
        now = time.time()
        dt = now - prev_time

        hand_tracker.update(dt)
        mouse_controller.update(hand_tracker.velocity, dt) #will need to scale this by delta time

        prev_time = now

        if keyboard.is_pressed('`'):
            print("exiting...`")
            break