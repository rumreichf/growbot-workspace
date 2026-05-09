import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import random
import time
import os

class RandomExplorer(Node):

    def __init__(self):
        super().__init__('random_explorer')
        self.publisher_ = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.timer = self.create_timer(10.0, self.send_goal)

    def send_goal(self):
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = random.uniform(-2, 2)
        goal.pose.position.y = random.uniform(-2, 2)
        goal.pose.orientation.w = 1.0

        self.publisher_.publish(goal)
        self.get_logger().info(f'Sending goal: {goal.pose.position.x}, {goal.pose.position.y}')

def main(args=None):
    rclpy.init(args=args)
    node = RandomExplorer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
