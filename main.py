#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from source.hand_gesture_app import HandGestureApp

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--width", help='cap width', type=int, default=960)
    parser.add_argument("--height", help='cap height', type=int, default=540)
    parser.add_argument('--use_static_image_mode', action='store_true')
    parser.add_argument("--min_detection_confidence", type=float, default=0.7)
    parser.add_argument("--min_tracking_confidence", type=int, default=0.5)
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    app = HandGestureApp(args)
    app.gui.root.mainloop()