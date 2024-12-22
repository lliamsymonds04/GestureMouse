
import time
import mouse

VELOCITY_SCALAR = 500

class MouseController:
    def __init__(self):
        pass

    def update(self, velocity: (float, float), dt: float):
        # pyautogui.moveRel(int(velocity[0] * VELOCITY_SCALAR), int(velocity[1] * VELOCITY_SCALAR),
        mouse.move(int(velocity[0] * VELOCITY_SCALAR), int(velocity[1] * VELOCITY_SCALAR), absolute=False)