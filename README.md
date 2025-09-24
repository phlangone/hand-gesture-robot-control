# Hand Gesture Robot Control

Hand Gesture Robot Control is a project that enables users to control a robot using hand gestures detected via computer vision and machine learning. The system captures hand movements through a camera, interprets gestures, and sends commands to the robot for real-time interaction.

## Features

- Real-time hand gesture recognition
- Seamless robot control via gesture commands
- Modular and extensible codebase
- Easy integration with various robot platforms

## Directory Structure

```
hand-gesture-robot-control/
├── models/              # Gesture recognition models and configs
├── robot/               # Robot control modules and interfaces
├── src/                 # Main application and gesture detection code
│   └── ...              # Source files
├── utils/               # Utilities functions
├── tests/               # Unit and integration tests
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation
```

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/hand-gesture-robot-control.git
    cd hand-gesture-robot-control
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Connect your camera and robot hardware.
2. Run the main application:
    ```bash
    python main.py
    ```
3. Perform supported hand gestures in front of the camera to control the robot.

## Supported Gestures

- Open palm: Enable robot operation
- Close palm: Disable robot 
- Move finger CW: Select program 1
- Move finger CCW: Select program 2

## Contributing

Contributions are welcome!

## Credits

- [sdurobotics/ur_rtde](https://gitlab.com/sdurobotics/ur_rtde.git) for Universal Robots RTDE communication.
- [kinivi/hand-gesture-recognition-mediapipe](https://github.com/kinivi/hand-gesture-recognition-mediapipe.git) for gesture recognition using MediaPipe.