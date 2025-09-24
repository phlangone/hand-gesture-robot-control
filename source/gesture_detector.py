import csv
import copy
import itertools
import cv2 as cv
import numpy as np
from collections import Counter
from collections import deque

import mediapipe as mp

from utils import CvFpsCalc
from model import KeyPointClassifier
from model import PointHistoryClassifier

class GestureDetector:
    def __init__(self, args):
        self.args = args
        
        # MediaPipe hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=args.use_static_image_mode,
            max_num_hands=1,
            min_detection_confidence=args.min_detection_confidence,
            min_tracking_confidence=args.min_tracking_confidence,
        )
        
        # Load classifiers
        self.keypoint_classifier = KeyPointClassifier()
        self.point_history_classifier = PointHistoryClassifier()
        
        # Load labels
        self.keypoint_classifier_labels = self._load_labels(
            'model/keypoint_classifier/keypoint_classifier_label.csv'
        )
        self.point_history_classifier_labels = self._load_labels(
            'model/point_history_classifier/point_history_classifier_label.csv'
        )
        
        # FPS calculator
        self.cvFpsCalc = CvFpsCalc(buffer_len=10)

    def _load_labels(self, filepath):
        """Load classifier labels from CSV"""
        with open(filepath, encoding='utf-8-sig') as f:
            return [row[0] for row in csv.reader(f)]

    def process_frame(self, image):
        """Process frame with MediaPipe"""
        image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        return self.hands.process(image_rgb)

    def calc_bounding_rect(self, image, landmarks):
        """Calculate bounding rectangle for hand"""
        image_width, image_height = image.shape[1], image.shape[0]
        landmark_array = np.empty((0, 2), int)
        
        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)
            landmark_point = [np.array((landmark_x, landmark_y))]
            landmark_array = np.append(landmark_array, landmark_point, axis=0)
            
        x, y, w, h = cv.boundingRect(landmark_array)
        return [x, y, x + w, y + h]

    def calc_landmark_list(self, image, landmarks):
        """Calculate landmark coordinates"""
        image_width, image_height = image.shape[1], image.shape[0]
        landmark_point = []
        
        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)
            landmark_point.append([landmark_x, landmark_y])
            
        return landmark_point

    def pre_process_landmark(self, landmark_list):
        """Pre-process landmarks for classification"""
        temp_landmark_list = copy.deepcopy(landmark_list)
        base_x, base_y = 0, 0
        
        for index, landmark_point in enumerate(temp_landmark_list):
            if index == 0:
                base_x, base_y = landmark_point[0], landmark_point[1]
            temp_landmark_list[index][0] -= base_x
            temp_landmark_list[index][1] -= base_y
            
        temp_landmark_list = list(itertools.chain.from_iterable(temp_landmark_list))
        max_value = max(list(map(abs, temp_landmark_list)))
        
        def normalize_(n):
            return n / max_value
            
        return list(map(normalize_, temp_landmark_list))

    def pre_process_point_history(self, image, point_history):
        """Pre-process point history for classification"""
        image_width, image_height = image.shape[1], image.shape[0]
        temp_point_history = copy.deepcopy(point_history)
        base_x, base_y = 0, 0
        
        for index, point in enumerate(temp_point_history):
            if index == 0:
                base_x, base_y = point[0], point[1]
            temp_point_history[index][0] = (temp_point_history[index][0] - base_x) / image_width
            temp_point_history[index][1] = (temp_point_history[index][1] - base_y) / image_height
            
        return list(itertools.chain.from_iterable(temp_point_history))

    def classify_static_gesture(self, landmark_list):
        """Classify static hand gesture"""
        pre_processed_landmark_list = self.pre_process_landmark(landmark_list)
        return self.keypoint_classifier(pre_processed_landmark_list)

    def classify_dynamic_gesture(self, image, point_history, history_length):
        """Classify dynamic hand gesture"""
        pre_processed_point_history_list = self.pre_process_point_history(image, point_history)
        point_history_len = len(pre_processed_point_history_list)
        
        if point_history_len == (history_length * 2):
            return self.point_history_classifier(pre_processed_point_history_list)
        return 0

    def get_static_gesture_label(self, hand_sign_id):
        """Get static gesture label"""
        if hand_sign_id < len(self.keypoint_classifier_labels):
            return self.keypoint_classifier_labels[hand_sign_id]
        return ""

    def get_dynamic_gesture_label(self, finger_gesture_history):
        """Get dynamic gesture label"""
        if finger_gesture_history:
            most_common_fg_id = Counter(finger_gesture_history).most_common()
            if most_common_fg_id and most_common_fg_id[0][0] < len(self.point_history_classifier_labels):
                return self.point_history_classifier_labels[most_common_fg_id[0][0]]
        return ""

    def draw_landmarks(self, image, landmark_point):
        """Draw hand landmarks on image"""
        if len(landmark_point) > 0:
            # Thumb
            self._draw_finger_segment(image, landmark_point, 2, 4)
            # Index finger
            self._draw_finger_segment(image, landmark_point, 5, 8)
            # Middle finger
            self._draw_finger_segment(image, landmark_point, 9, 12)
            # Ring finger
            self._draw_finger_segment(image, landmark_point, 13, 16)
            # Little finger
            self._draw_finger_segment(image, landmark_point, 17, 20)
            # Palm
            self._draw_palm_segments(image, landmark_point)
            
            # Key Points
            for index, landmark in enumerate(landmark_point):
                radius = 8 if index in [4, 8, 12, 16, 20] else 5
                cv.circle(image, (landmark[0], landmark[1]), radius, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), radius, (0, 0, 0), 1)
                
        return image

    def _draw_finger_segment(self, image, landmarks, start_idx, end_idx):
        """Draw finger segments"""
        for i in range(start_idx, end_idx):
            cv.line(image, tuple(landmarks[i]), tuple(landmarks[i+1]), (0, 0, 0), 6)
            cv.line(image, tuple(landmarks[i]), tuple(landmarks[i+1]), (255, 255, 255), 2)

    def _draw_palm_segments(self, image, landmarks):
        """Draw palm connecting segments"""
        connections = [(0,1), (1,2), (2,5), (5,9), (9,13), (13,17), (17,0)]
        for start_idx, end_idx in connections:
            cv.line(image, tuple(landmarks[start_idx]), tuple(landmarks[end_idx]), (0, 0, 0), 6)
            cv.line(image, tuple(landmarks[start_idx]), tuple(landmarks[end_idx]), (255, 255, 255), 2)

    def draw_info_text(self, image, brect, handedness, hand_sign_text, finger_gesture_text):
        """Draw information text on image"""
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)
        info_text = handedness.classification[0].label[0:]
        if hand_sign_text != "":
            info_text = info_text + ':' + hand_sign_text
        cv.putText(image, info_text, (brect[0] + 5, brect[1] - 4), 
                  cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
        
        if finger_gesture_text != "":
            cv.putText(image, "Gesture:" + finger_gesture_text, (10, 60), 
                      cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
            cv.putText(image, "Gesture:" + finger_gesture_text, (10, 60), 
                      cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv.LINE_AA)
        return image

    def draw_point_history(self, image, point_history):
        """Draw point history trail (finger movement path)"""
        for index, point in enumerate(point_history):
            if point[0] != 0 and point[1] != 0:
                # Draw green circles that get slightly larger for more recent points
                cv.circle(image, (point[0], point[1]), 1 + int(index / 2), (152, 251, 152), 2)
        return image

    def draw_info(self, image, fps):
        """Draw FPS information"""
        cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
        cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv.LINE_AA)
        return image