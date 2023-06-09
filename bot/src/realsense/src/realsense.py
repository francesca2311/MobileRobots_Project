#!/bin/python3

import rospy
from pathlib import Path
import cv2 as cv
import cv_bridge
from sensor_msgs.msg import Image, CompressedImage
from threading import Thread
import asyncio
import websockets
import numpy as np

class Node:
    def __init__(self) -> None:
        rospy.init_node(NODE_NAME, anonymous=True)
        self.rate = rospy.Rate(rospy.get_param("/camera/fps_publish"))

        # TODO: This has to be changed
        asyncio.get_event_loop().run_until_complete(self.publish_frame_cb(0))
        asyncio.get_event_loop().run_until_complete(self.publish_frame_cb(1))

    def set_camera(self):
        '''
        These lines of code are setting the properties of the camera stream using OpenCV's
        cv.VideoCapture()` method. Specifically, it is setting the frames per second (FPS) of the camera
        stream to the value specified in the ROS parameter `/camera/fps_capture`, and setting the frame
        width and height to the values specified in the ROS parameters `/camera/width` and `/camera/height`,
        respectively.
        '''
        self.cap.set(cv.CAP_PROP_FPS, rospy.get_param("/camera/fps_capture"))
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, rospy.get_param("/camera/width"))    
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, rospy.get_param("/camera/height"))   

    def print_camera_info(self, camera_id):
        '''
        These lines of code are retrieving the width, height, and frames per second (FPS) of the
        camera stream using OpenCV's `cv.VideoCapture()` method. The values are then logged using
        `rospy.loginfo()`.
        '''
        width = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)
        height = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)
        fps = self.cap.get(cv.CAP_PROP_FPS)
        rospy.loginfo(f"Frame size width x height: {int(width)}x{int(height)}@{fps} for camera: {camera_id}")
    
    async def publish_frame_cb(self, camera_id):
        '''
        This code is running in a separate thread and continuously checking if the ROS node is still running
        using `rospy.is_shutdown()`. If the node is still running and there is a new frame available in
        `self.frame`, it publishes the frame as a compressed image message to the ROS topic `"image"` using
        the `self.publish_frame()` method. It then sleeps for a duration of time specified by `self.rate`
        before checking again. This ensures that frames are continuously published to the ROS network at a
        consistent rate.
        '''
        self.cap = cv.VideoCapture(camera_id)
        self.set_camera()
        self.print_camera_info()

        ws = await websockets.connect('ws://192.168.178.65:8000')

        while not rospy.is_shutdown():
            ret, frame = self.cap.read()

            if frame is None:
                continue

            frame_with_id = np.vstack((np.array([camera_id]), frame))  # Add camera ID to the image
            _, image_buffer = cv.imencode('.jpg', frame_with_id)
            await ws.send(image_buffer.tobytes())
            self.rate.sleep()

    
if __name__ == "__main__":
    NODE_NAME = "realsense_node"
    node = Node()