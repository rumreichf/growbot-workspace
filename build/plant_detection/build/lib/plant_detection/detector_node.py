import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge

from ultralytics import YOLO
from tf2_ros import Buffer, TransformListener

import cv2
import os
import json
import math


class PlantDetector(Node):

    def __init__(self):
        super().__init__('plant_detector')

        # Camera intrinsics
        self.fx = 530.4669406576809
        self.fy = 530.4669406576809
        self.cx = 320.5
        self.cy = 240.5

        self.detected_plants = []

        self.save_path = os.path.expanduser("~/ros2_ws/plants.json")

        # RGB image
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.callback,
            10
        )

        # Depth image
        self.depth_image = None
        self.depth_sub = self.create_subscription(
            Image,
            '/camera/depth/image_raw',
            self.depth_callback,
            10
        )

        self.bridge = CvBridge()

        # YOLO model
        self.model = YOLO(
            os.path.expanduser(
                "~/ros2_ws/yolov8/runs/detect/yolov8_potted_plants-12/weights/best.pt"
            )
        )

        # TF
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.get_logger().info("Plant detector node started.")

    # ---------------- SAVE ----------------
    def save_plants(self):
        self.get_logger().info(f"Saving plants to: {self.save_path}")
        print("DEBUG SAVE HIT")

        with open(self.save_path, 'w') as f:
            json.dump(self.detected_plants, f, indent=4)

    # ---------------- DUPLICATE CHECK ----------------
    def already_detected(self, x, y):
        for plant in self.detected_plants:
            dist = math.sqrt((x - plant['x'])**2 + (y - plant['y'])**2)
            if dist < 0.75:
                return True
        return False

    # ---------------- RGB CALLBACK ----------------
    def callback(self, msg):

        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

        results = self.model(frame)
        annotated = results[0].plot()
        boxes = results[0].boxes

        for box in boxes:

            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            confidence = float(box.conf[0])

            if confidence < 0.6:
                continue

            x1, y1, x2, y2 = box.xyxy[0]
            u = int((x1 + x2) / 2)
            v = int((y1 + y2) / 2)

            cam_point = self.estimate_ground_point(u, v)

            if cam_point is None:
                continue

            cam_stamped = PoseStamped()
            cam_stamped.header.frame_id = "camera_rgb_optical_frame"
            cam_stamped.header.stamp = self.get_clock().now().to_msg()

            cam_stamped.pose.position.x = cam_point['x']
            cam_stamped.pose.position.y = cam_point['y']
            cam_stamped.pose.position.z = cam_point['z']
            cam_stamped.pose.orientation.w = 1.0

            try:
                map_pose = self.tf_buffer.transform(cam_stamped, "map")

                plant_map_x = map_pose.pose.position.x
                plant_map_y = map_pose.pose.position.y

            except Exception as e:
                self.get_logger().warn(f"TF failed: {e}")
                continue

            # ---------------- PLANT LOGIC ----------------
            if self.already_detected(plant_map_x, plant_map_y):
                continue

            plant = {
                'type': class_name,
                'x': plant_map_x,
                'y': plant_map_y
            }

            self.detected_plants.append(plant)
            self.save_plants()

            self.get_logger().info(
                f"Plant detected: {class_name} at ({plant_map_x:.2f}, {plant_map_y:.2f})"
            )

        cv2.imshow("Plant Detection", annotated)
        cv2.waitKey(1)

    # ---------------- DEPTH CALLBACK ----------------
    def depth_callback(self, msg):
        self.depth_image = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='passthrough'
        )

    # ---------------- DEPTH ESTIMATION ----------------
    def estimate_ground_point(self, u, v):

        if self.depth_image is None:
            return None

        try:
            depth = self.depth_image[v, u]
        except IndexError:
            return None

        if depth == 0:
            return None

        Z = float(depth)

        # convert mm → meters if needed
        if Z > 100:
            Z = Z / 1000.0

        X = (u - self.cx) * Z / self.fx
        Y = (v - self.cy) * Z / self.fy

        return {
            'x': X,
            'y': Y,
            'z': Z
        }


def main(args=None):
    rclpy.init(args=args)
    node = PlantDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
