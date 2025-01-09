from typing import Any

import cv2
from numpy import ndarray, dtype

WINDOW_NAME = "Camera"

def init():
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

def update(img: ndarray[Any, dtype], state: str):
    x,y,w,h = cv2.getWindowImageRect(WINDOW_NAME)
    cv2.putText(img, state, (50, int(h * 0.9)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.imshow(WINDOW_NAME, img)