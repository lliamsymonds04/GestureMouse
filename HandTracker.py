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

HAND_TO_TRACK = "Right"

class HandTracker:
    def __init__(self, model_path: str, debug_mode: bool = False):
        # self.cap = cv2.VideoCapture(0)
        for i in range(3):
            cap = cv2.VideoCapture(i)
            ret = cap.read()
            if ret[0]:
                print(f"Camera {i} selected")
                self.cap = cap
                break


        self.start_time = time.time()
        self.previous_time = self.start_time
        self.model_path = model_path
        self.debug_mode = debug_mode

        # Initialize Mediapipe components
        self.mp_hands = mediapipe.solutions.hands
        self.mp_drawing = mediapipe.solutions.drawing_utils
        self.landmark_result = None
        self.processing_hand = False
        self.can_see_hand = False

        self.trackers = {
            "index finger": PointTracker(1,8),
            "middle finger": PointTracker(1, 12),
            "ring finger": PointTracker(3, 16),
            "pinky finger": PointTracker(3, 20),
            "index knuckle": PointTracker(3, 5),
            "middle knuckle": PointTracker(3, 9),
            "ring knuckle": PointTracker(3, 13),
            "pinky knuckle": PointTracker(3, 17),
            "thumb": PointTracker(1, 4),
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

        # if debug_mode:
        #     cv2.namedWindow(DEBUG_WINDOW_NAME, cv2.WINDOW_NORMAL)


    def handle_detection(self, result: HandLandmarkerResult, output_image: mediapipe.Image, timestamp_ms: int):
        self.landmark_result = result
        self.processing_hand = False

    def update(self):
        ret, frame = self.cap.read()

        if not ret:
            print("Failed to grab frame")
            return

        mp_image = mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=numpy.array(frame))
        mp_image_np = numpy.array(mp_image.numpy_view())

        # Call the async detection method
        now = time.time()
        if not self.processing_hand:
            self.processing_hand = True
            self.landmarker.detect_async(mp_image, timestamp_ms=int((now - self.start_time) * 1000))

        height, width, depth = frame.shape

        detected_hand = False
        if self.landmark_result is not None:
            result: HandLandmarkerResult = self.landmark_result


            landmarks = None
            if len(result.handedness) == 1:
                hand = result.handedness[0][0]
                # print(hand.display_name)
                if hand.display_name != HAND_TO_TRACK: #mediapipe labels the hands wrong
                    landmarks = result.hand_landmarks[0]
                    detected_hand = True

            elif len(result.handedness) == 2:
                x_positions = [0,0]
                for handedness in result.handedness:
                    hand = handedness[0]

                    hand_landmarks = result.hand_landmarks[hand.index]
                    marker = hand_landmarks[0]
                    x_positions[hand.index] = marker.x

                hand_index = 0
                if HAND_TO_TRACK == "Right":
                    hand_index = x_positions[0] < x_positions[1] and 1 or 0
                elif HAND_TO_TRACK == "Left":
                    hand_index = x_positions[0] < x_positions[1] and 0 or 1

                landmarks = result.hand_landmarks[hand_index]
                detected_hand = True

            if self.debug_mode:
                cv2.putText(mp_image_np, f"hands detected: {len(result.handedness)}", (300, int(height * 0.9)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


            if landmarks is not None:
                #update the point trackers
                for _, tracker in self.trackers.items():
                    mark = landmarks[tracker.landmark_index]
                    tracker.update_point(mark.x, mark.y, mark.z)

        if not detected_hand:
            for _, tracker in self.trackers.items():
                tracker.update_point(tracker.x, tracker.y, tracker.z) #pass the same point so it stays stationary

        # update previous position
        self.previous_time = now
        self.can_see_hand = detected_hand


        if self.debug_mode:

            if detected_hand:
                height, width, depth = frame.shape

                for _, tracker in self.trackers.items():
                    x,y = int(tracker.x  * width), int(tracker.y * height)

                    cv2.circle(mp_image_np, (x, y), 10, (255, 0, 0), 2)

        return mp_image_np

    def close(self):
        self.cap.release()
        if self.debug_mode:
            cv2.destroyAllWindows()