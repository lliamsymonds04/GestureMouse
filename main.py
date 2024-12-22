import time

from HandTracker import HandTracker

if __name__ == "__main__":
    pass

    hand_tracker = HandTracker(model_path='Models\\hand_landmarker.task')


    prev_time = time.time()
    while True:
        now = time.time()
        dt = now - prev_time