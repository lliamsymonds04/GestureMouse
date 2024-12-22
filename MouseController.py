import pyautogui

VELOCITY_SCALAR = 50

class MouseController:
    def __init__(self):
        pass

    def update(self, velocity: (float, float)):
        pyautogui.moveRel(int(velocity[0] * VELOCITY_SCALAR), int(velocity[1] * VELOCITY_SCALAR))