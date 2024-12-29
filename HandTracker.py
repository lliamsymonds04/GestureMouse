import cv2
import mediapipe
import numpy
import time
import collections

from PointTracker import PointTracker

BaseOptions = mediapipe.tasks.BaseOptions
HandLandmarker = mediapipe.tasks.vision.HandLandmarker
HandLandmarkerOptions = mediapipe.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mediapipe.tasks.vision.HandLandmarkerResult
VisionRunningMode = mediapipe.tasks.vision.RunningMode

DEBUG_WINDOW_NAME = "Camera"
HAND_TO_TRACK = "right"

#flip the hand bc media pipe labels them wrong
if HAND_TO_TRACK.lower() == "right":
    HAND_TO_TRACK = "Left"
else:
    HAND_TO_TRACK = "Right"

class HandTracker:
    def __init__(self, model_path: str, debug_mode: bool = False):
        self.cap = cv2.VideoCapture(0)
        self.start_time = time.time()
        self.previous_time = self.start_time
        self.model_path = model_path
        self.debug_mode = debug_mode

        # Initialize Mediapipe components
        self.mp_hands = mediapipe.solutions.hands
        self.mp_drawing = mediapipe.solutions.drawing_utils
        self.landmark_result = None
        self.processing_hand = False

        self.trackers = {
            "index finger": PointTracker(3,8),
            "middle finger": PointTracker(3, 12),
            "ring finger": PointTracker(3, 16),
            "pinky finger": PointTracker(3, 20),
            "index knuckle": PointTracker(3, 5),
            "middle knuckle": PointTracker(3, 9),
            "ring knuckle": PointTracker(3, 13),
            "pinky knuckle": PointTracker(3, 17),
            "wrist": PointTracker(3,0),
        }

        options = mediapipe.tasks.vision.HandLandmarkerOptions(
            base_options=mediapipe.tasks.BaseOptions(model_asset_path=self.model_path),
            running_mode=mediapipe.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=2,
            result_callback=self.handle_detection,
            min_tracking_confidence=0.5,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
        )

        self.landmarker = mediapipe.tasks.vision.HandLandmarker.create_from_options(options)

        if debug_mode:
            cv2.namedWindow(DEBUG_WINDOW_NAME, cv2.WINDOW_NORMAL)


    def handle_detection(self, result: HandLandmarkerResult, output_image: mediapipe.Image, timestamp_ms: int):
        self.landmark_result = result
        self.processing_hand = False

    #going to need delta time
    def update(self, dt: float):
        ret, frame = self.cap.read()

        if not ret:
            print("Failed to grab frame")
            return

        mp_image = mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=numpy.array(frame))

        # Call the async detection method
        now = time.time()
        if not self.processing_hand:
            self.processing_hand = True
            self.landmarker.detect_async(mp_image, timestamp_ms=int((now - self.start_time) * 1000))

        detected_hand = False
        if self.landmark_result is not None:
            result: HandLandmarkerResult = self.landmark_result

            for handedness in result.handedness:
                hand = handedness[0]
                if detected_hand or hand.display_name != HAND_TO_TRACK:
                    continue

                detected_hand = True

                if len(result.hand_landmarks) > 1:
                    landmarks = result.hand_landmarks[hand.index]
                else:
                    landmarks = result.hand_landmarks[0]

                #update the point trackers
                for _, tracker in self.trackers.items():
                    mark = landmarks[tracker.landmark_index]
                    tracker.update_point(mark.x, mark.y, mark.z)

        if not detected_hand:
            for _, tracker in self.trackers.items():
                tracker.update_point(tracker.x, tracker.y, tracker.z) #pass the same point so it stays stationary

        # update previous position
        self.previous_time = now

        if self.debug_mode:
            mp_image_np = numpy.array(mp_image.numpy_view())

            if detected_hand:
                height, width, depth = frame.shape

                for _, tracker in self.trackers.items():
                    x,y = int(tracker.x  * width), int(tracker.y * height)

                    cv2.circle(mp_image_np, (x, y), 10, (255, 0, 0), 2)

            cv2.imshow(DEBUG_WINDOW_NAME, mp_image_np)


    def close(self):
        self.cap.release()
        if self.debug_mode:
            cv2.destroyAllWindows()