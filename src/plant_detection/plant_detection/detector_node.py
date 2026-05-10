import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
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

        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.callback,
            10
        )

        self.bridge = CvBridge()

        self.model = YOLO(
            os.path.expanduser(
                "~/growbot-workspace/yolov8/runs/detect/yolov8_potted_plants-12/weights/best.pt"
            )
        )

        # TF listener
        self.tf_buffer = Buffer()

        self.tf_listener = TransformListener(
            self.tf_buffer,
            self
        )

        # Stored plant detections
        self.detected_plants = []

        self.get_logger().info(
            "Plant detector node started."
        )

    def save_plants(self):

        with open(self.save_path, 'w') as f:

            json.dump(
                self.detected_plants,
                f,
                indent=4
            )

    def already_detected(self, x, y):

        for plant in self.detected_plants:

            dist = math.sqrt(
                (x - plant['x'])**2 +
                (y - plant['y'])**2
            )

            if dist < 1.0:
                return True

        return False

    def callback(self, msg):

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            'bgr8'
        )

        results = self.model(frame)

        annotated = results[0].plot()

        boxes = results[0].boxes

        for box in boxes:

            class_id = int(box.cls[0])

            class_name = self.model.names[class_id]

            confidence = float(box.conf[0])

            if confidence < 0.6:
                continue

            try:

                transform = self.tf_buffer.lookup_transform(
                    'map',
                    'base_link',
                    rclpy.time.Time()
                )

                robot_x = (
                    transform.transform.translation.x
                )

                robot_y = (
                    transform.transform.translation.y
                )

                if self.already_detected(
                    robot_x,
                    robot_y
                ):
                    continue

                plant = {
                    'type': class_name,
                    'x': robot_x,
                    'y': robot_y
                }

                self.detected_plants.append(
                    plant
                )

                self.save_plants()

                self.get_logger().info(
                    f"Plant detected: "
                    f"{class_name} "
                    f"at "
                    f"({robot_x:.2f}, {robot_y:.2f})"
                )

            except Exception as e:

                self.get_logger().warn(
                    f"TF lookup failed: {e}"
                )

        cv2.imshow(
            "Plant Detection",
            annotated
        )

        cv2.waitKey(1)


def main(args=None):

    rclpy.init(args=args)

    node = PlantDetector()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
