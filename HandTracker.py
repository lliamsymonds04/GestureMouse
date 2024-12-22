import cv2
import mediapipe
import numpy
import time


BaseOptions = mediapipe.tasks.BaseOptions
HandLandmarker = mediapipe.tasks.vision.HandLandmarker
HandLandmarkerOptions = mediapipe.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mediapipe.tasks.vision.HandLandmarkerResult
VisionRunningMode = mediapipe.tasks.vision.RunningMode



class HandTracker:
    def __init__(self, model_path: str):
        self.cap = cv2.VideoCapture(0)
        self.start_time = time.time()
        self.previous_time = self.start_time
        self.model_path = model_path

        # Initialize Mediapipe components
        self.mp_hands = mediapipe.solutions.hands
        self.mp_drawing = mediapipe.solutions.drawing_utils
        self.landmark_result = None

        self.previous_position = None
        self.velocity = (0,0)

        options = mediapipe.tasks.vision.HandLandmarkerOptions(
            base_options=mediapipe.tasks.BaseOptions(model_asset_path=self.model_path),
            running_mode=mediapipe.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=1,
            result_callback=self.handle_detection,
            min_tracking_confidence=0.4,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
        )

        self.landmarker = mediapipe.tasks.vision.HandLandmarker.create_from_options(options)

        #need a shadowing method to track position
        #need to track change in velocity


    def handle_detection(self, result: HandLandmarkerResult, output_image: mediapipe.Image, timestamp_ms: int):
        self.landmark_result = result

    #going to need delta time
    def update(self):
        ret, frame = self.cap.read()

        mp_image = mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=numpy.array(frame))

        # Call the async detection method
        now = time.time()
        self.landmarker.detect_async(mp_image, timestamp_ms=int((now - self.start_time) * 1000))

        dt = now - self.previous_time

        if self.landmark_result is not None:
            result: HandLandmarkerResult = self.landmark_result

            if len(result.handedness) > 0:
                hand_info = result.handedness[0][0]
                landmarks = result.hand_landmarks[0]

                index_knuckle = landmarks[5]

                if self.previous_position is not None:
                    displacement = (index_knuckle.x - self.previous_position.x, index_knuckle.y - self.previous_position.y)
                    self.velocity = (displacement[0]/dt, displacement[1]/dt)


                self.previous_position = index_knuckle

        #update previous position
        self.previous_time = now