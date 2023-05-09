#! /usr/bin/python3
import rospy
from move_base_msgs.msg import MoveBaseActionResult
from geometry_msgs.msg import PoseStamped
import csv
import os
from std_msgs.msg import String, Int32MultiArray
import random
from geometry_msgs.msg import Twist
import numpy as np 
import math
import tf

class Move:
    def __init__(self) -> None:
        self.msg = PoseStamped()
        self.waiting = False
        self.next_command = None
        self.listener = tf.TransformListener()
        self.pub_goal = rospy.Publisher("move_base_simple/goal", PoseStamped, queue_size=10)
        self.pub_cmd = rospy.Publisher('cmd_vel', Twist, queue_size=10)
        self.pub_next_waypoint = rospy.Publisher('next_waypoint', Int32MultiArray, queue_size=10)
        #self.sub = rospy.Subscriber("qr_most_common", String, self.callback_command)
        self.sub = rospy.Subscriber("qr_data_topic", String, self.callback_command)
        rospy.sleep(3.0)

    # Incrementation of dict commands
    def callback_command(self, msg):
        self.next_command = msg

    # Send next waypoint to reach
    def send_goal(self,x,y):
        self.msg.header.frame_id = "map"
        self.msg.pose.position.x = float(x)
        self.msg.pose.position.y = float(y)
        #self.msg.pose.orientation.w = 1.0
        self.pub_goal.publish(self.msg)
        #print(f"{self.msg.__str__()}")
    
    # Calibrate robot 
    def calibration(self):
        forward_msg = Twist()
        backward_msg = Twist()
        rotation_right = Twist()
        rotation_left = Twist()
        forward_msg.linear.x = 0.2
        backward_msg.linear.x = -0.2
        self.pub_cmd.publish(forward_msg)
        rospy.sleep(2)  
        self.pub_cmd.publish(backward_msg)
        rospy.sleep(2)
        forward_msg.linear.x = 0.3
        backward_msg.linear.x = -0.3
        self.pub_cmd.publish(forward_msg)
        rospy.sleep(2)  
        self.pub_cmd.publish(backward_msg)
        rospy.sleep(2)
        
        rotation_right.angular.z = 0.5
        rotation_left.angular.z = -0.5
        self.pub_cmd.publish(rotation_right)
        rospy.sleep(2)  
        self.pub_cmd.publish(rotation_left)
        rospy.sleep(2) 

        stop_msg = Twist()
        self.pub_cmd.publish(stop_msg)

    # Find nearest waypoint due to the command recognized
    def find_nearest_point(self, points, current_location, orientation, command):
        # Create a dictionary of command vectors with their corresponding angles
        command_vectors = {
            'right': np.array([math.cos(math.radians(orientation + 90)), math.sin(math.radians(orientation + 90))]),
            'left': np.array([math.cos(math.radians(orientation - 90)), math.sin(math.radians(orientation - 90))]),
            'straight on': np.array([math.cos(math.radians(orientation)), math.sin(math.radians(orientation))]),
            'go back': np.array([math.cos(math.radians(orientation + 180)), math.sin(math.radians(orientation + 180))])
        }

        # Calculate the angle and distance between each point and the current location
        angles = []
        distances = []
        for point in points:
            point_vector = np.array([point[0] - current_location[0], point[1] - current_location[1]])
            norm_point = np.linalg.norm(point_vector)
            forward_vector = command_vectors[command]
            d_angle = math.degrees(math.atan2(np.cross(forward_vector, point_vector), np.dot(forward_vector, point_vector)))
            angles.append(d_angle)
            distances.append(norm_point)

        # Find the nearest point in the desired direction
        if command == 'right':
            index = np.argmin(np.array(angles))
        elif command == 'left':
            index = np.argmax(np.array(angles))
        elif command == 'straight on':
            index = np.argmin(np.array(distances))
        elif command == 'go back':
            index = np.argmax(np.array(distances))

        return points[index]

    # Get robot position 
    def get_robot_position(self):
        try:
            # ------- Cerca il transform tra i frame di riferimento della posizione del robot e della mappa
            (trans, rot) = self.listener.lookupTransform('/map', '/base_link', rospy.Time(0))
            print('Robot position: {}'.format(trans))
            print('Robot orientation: {}'.format(tf.transformations.euler_from_quaternion(rot)))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            pass
        return trans, rot

    # TO DO: call service to return command
    # Move the robot to the goal and return the command recognized
    def goal_reached(self,next_goal):
        self.send_goal(next_goal[0],next_goal[1])
        rospy.loginfo("Goal send")
        rospy.wait_for_message("move_base/result", MoveBaseActionResult)
        rospy.loginfo("Goal reached")
        
    def move(self,command):
        trans, rot = self.get_robot_position()
        # First command, go straight 
        next_waypoint = self.find_nearest_point(waypoints, trans, rot[2],command)
        print(f"Next waypoint: {next_waypoint}")
        self.pub_next_waypoint.publish(Int32MultiArray(data=next_waypoint))
        self.goal_reached(next_waypoint)


if __name__ == "__main__":
    rospy.init_node("goal_custom")
    navigation = Move()
    rate = rospy.Rate(10.0)
    waypoints = []
    # Read waypoints
    with open('/home/francesca/Scrivania/MobileRobots_Project/bot/src/navigation/src/waypoints.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            waypoints.append((float(row[0]), float(row[1])))

    # Calibration
    navigation.calibration()
    print("CALIBRATION DONE")
    navigation.move('straight on')
    navigation.move(navigation.next_command)
    rospy.spin()

'''
    def compute_magnitude_angle_with_sign(target_location, current_location, orientation):
        """
        Compute relative angle and distance between a target_location and a current_location

            :param target_location: location of the target object
            :param current_location: location of the reference object
            :param orientation: orientation of the reference object
            :return: a tuple composed by the distance to the object and the angle between both objects
        """
        target_vector = np.array([target_location.x - current_location.x, target_location.y - current_location.y])
        norm_target = np.linalg.norm(target_vector)
        forward_vector = np.array([math.cos(math.radians(orientation)), math.sin(math.radians(orientation))])

        d_angle = math.degrees(math.atan2(np.cross(forward_vector, target_vector), np.dot(forward_vector, target_vector)))
        return (norm_target, d_angle)
'''