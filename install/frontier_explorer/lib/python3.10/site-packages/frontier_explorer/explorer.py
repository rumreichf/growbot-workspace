import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from nav_msgs.msg import Odometry, OccupancyGrid
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped

import random
import math


class FrontierExplorer(Node):

    def __init__(self):
        super().__init__('frontier_explorer')

        self.robot_x = 0.0
        self.robot_y = 0.0

        self.map_data = None

        self.goal_active = False

        self.failed_goals = []

        self.no_frontier_count = 0

        self.MIN_FRONTIER_COUNT = 10
        self.MIN_GOAL_DISTANCE = 1.0

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10
        )

        self.nav_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose'
        )

        self.get_logger().info("Waiting for Nav2...")
        self.nav_client.wait_for_server()
        self.get_logger().info("Nav2 ready")

        self.timer = self.create_timer(5.0, self.explore)

        self.get_logger().info("Frontier Explorer Started")

    def odom_callback(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

    def map_callback(self, msg):
        self.map_data = msg

    def find_frontiers(self, grid, width, height):

        frontiers = []

        for y in range(1, height - 1):
            for x in range(1, width - 1):

                i = y * width + x

                if grid[i] != 0:
                    continue

                neighbors = [
                    grid[i + 1],
                    grid[i - 1],
                    grid[i + width],
                    grid[i - width]
                ]

                if -1 in neighbors:
                    frontiers.append((x, y))

        return frontiers

    def is_goal_valid(self, x, y):

        dist = math.sqrt(
            (x - self.robot_x) ** 2 +
            (y - self.robot_y) ** 2
        )

        if dist < self.MIN_GOAL_DISTANCE:
            return False

        for gx, gy in self.failed_goals:

            failed_dist = math.sqrt(
                (x - gx) ** 2 +
                (y - gy) ** 2
            )

            if failed_dist < 1.0:
                return False

        return True

    def send_goal(self, x, y):

        self.goal_active = True

        goal = NavigateToPose.Goal()

        pose = PoseStamped()

        pose.header.frame_id = "map"
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)

        pose.pose.orientation.w = 1.0

        goal.pose = pose

        self.get_logger().info(
            f"Sending Nav2 goal: ({x:.2f}, {y:.2f})"
        )

        self.nav_client.send_goal_async(
            goal
        ).add_done_callback(
            self.goal_response_callback
        )

    def explore(self):

        if self.map_data is None:
            return

        if self.goal_active:
            return

        grid = self.map_data.data
        width = self.map_data.info.width
        height = self.map_data.info.height

        frontiers = self.find_frontiers(
            grid,
            width,
            height
        )

        if len(frontiers) < self.MIN_FRONTIER_COUNT:

            self.no_frontier_count += 1

            self.get_logger().info(
                f"Few frontiers remaining: {len(frontiers)}"
            )

            if self.no_frontier_count > 5:
                self.get_logger().info(
                    "Exploration complete!"
                )

            return

        else:
            self.no_frontier_count = 0

        random.shuffle(frontiers)

        origin = self.map_data.info.origin.position
        res = self.map_data.info.resolution

        for frontier in frontiers:

            x = origin.x + frontier[0] * res
            y = origin.y + frontier[1] * res

            if self.is_goal_valid(x, y):

                self.send_goal(x, y)
                return

        self.get_logger().info(
            "No valid frontier goals found"
        )

    def goal_response_callback(self, future):

        goal_handle = future.result()

        if not goal_handle.accepted:

            self.get_logger().info(
                "Goal rejected"
            )

            self.goal_active = False
            return

        self.get_logger().info(
            "Goal accepted"
        )

        goal_handle.get_result_async().add_done_callback(
            self.goal_result_callback
        )

    def goal_result_callback(self, future):

        result = future.result().result

        status = future.result().status

        self.get_logger().info(
            f"Goal finished with status: {status}"
        )

        if status != 4:
            pass
        else:
            self.failed_goals.append(
                (self.robot_x, self.robot_y)
            )

            self.get_logger().info(
                "Goal failed, blacklisting area"
            )

        self.goal_active = False


def main():

    rclpy.init()

    node = FrontierExplorer()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
