import cv2 as cv
import copy
import time
from collections import deque

from .robot_controller import RobotController
from .gesture_detector import GestureDetector
from .gui_interface import GUIInterface
from .fsm_controller import FSMController, FSMState

class HandGestureApp:
    def __init__(self, args):
        self.args = args
        
        # Initialize components
        self.robot_controller = RobotController(host='192.168.0.160')
        self.gesture_detector = GestureDetector(args)
        self.gui = GUIInterface()
        self.fsm_controller = FSMController()
        
        # Camera setup
        self.cap = cv.VideoCapture(args.device)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)
        
        # History buffers
        self.history_length = 16
        self.point_history = deque(maxlen=self.history_length)
        self.finger_gesture_history = deque(maxlen=self.history_length)
        
        # Connect GUI callbacks
        self.gui.set_on_closing_callback(self.on_closing)
        
        # Start the main loop
        self.gui.log_message("Aplicação iniciada. Aguardando gestos.")
        self.update_frame()

    def update_frame(self):
        """Main processing loop"""
        fps = self.gesture_detector.cvFpsCalc.get()

        ret, image = self.cap.read()
        if not ret:
            self.gui.root.after(10, self.update_frame)
            return
            
        image = cv.flip(image, 1)
        debug_image = copy.deepcopy(image)
        
        # Process gestures
        results = self.gesture_detector.process_frame(image)
        current_static_gesture, current_dynamic_gesture = "", ""
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, 
                                                results.multi_handedness):
                # Process hand landmarks
                landmark_list = self.gesture_detector.calc_landmark_list(debug_image, hand_landmarks)
                brect = self.gesture_detector.calc_bounding_rect(debug_image, hand_landmarks)
                
                # Classify gestures
                hand_sign_id = self.gesture_detector.classify_static_gesture(landmark_list)
                
                # Update point history
                if hand_sign_id == 2:  # Pointing gesture
                    self.point_history.append(landmark_list[8])
                else:
                    self.point_history.append([0, 0])
                
                # Classify dynamic gesture
                finger_gesture_id = self.gesture_detector.classify_dynamic_gesture(
                    debug_image, self.point_history, self.history_length
                )
                self.finger_gesture_history.append(finger_gesture_id)
                
                # Get gesture labels
                current_static_gesture = self.gesture_detector.get_static_gesture_label(hand_sign_id)
                dynamic_label = self.gesture_detector.get_dynamic_gesture_label(self.finger_gesture_history)
                
                if "Counter" in dynamic_label:
                    current_dynamic_gesture = 'CCW'
                elif "Clockwise" in dynamic_label:
                    current_dynamic_gesture = 'CW'

                if "Close" in current_static_gesture: 
                    current_static_gesture = 'Close'
                elif "Open" in current_static_gesture: 
                    current_static_gesture = 'Open'
                
                # Draw visualization
                debug_image = self.gesture_detector.draw_landmarks(debug_image, landmark_list)
                debug_image = self.gesture_detector.draw_info_text(
                    debug_image, brect, handedness, current_static_gesture, dynamic_label
                )
        else:
            self.point_history.append([0, 0])
        
        # Draw finger movement and video FPS
        debug_image = self.gesture_detector.draw_point_history(debug_image, self.point_history)
        debug_image = self.gesture_detector.draw_info(debug_image, int(fps))
        
        # Update FSM
        self.fsm_controller.update(
            current_static_gesture, 
            current_dynamic_gesture, 
            self.robot_controller
        )

        # Convert to RGB
        debug_image_rgb = cv.cvtColor(debug_image, cv.COLOR_BGR2RGB)
        
        # Update GUI
        self.gui.update_display(
            debug_image_rgb,
            self.fsm_controller.state.name,
            current_static_gesture,
            current_dynamic_gesture,
            self.fsm_controller.pending_selection,
            self.fsm_controller.get_log_messages()
        )
        
        # Continue loop
        self.gui.root.after(10, self.update_frame)

    def on_closing(self):
        """Cleanup resources"""
        self.gui.log_message("Fechando a aplicação...")
        self.robot_controller.cleanup()
        self.cap.release()
        self.gui.cleanup()

    @property
    def root(self):
        """Provide access to the root window for main.py"""
        return self.gui.root
