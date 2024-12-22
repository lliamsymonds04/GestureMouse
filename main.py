import time

from HandTracker import HandTracker
from MouseController import MouseController

if __name__ == "__main__":
    pass

    hand_tracker = HandTracker(model_path='Models\\hand_landmarker.task')
    mouse_controller = MouseController()

    # prev_time = time.time()
    while True:
        # now = time.time()
        # dt = now - prev_time
        time.sleep(1/60)
        hand_tracker.update()
        mouse_controller.update(hand_tracker.velocity) #will need to scale this by delta time