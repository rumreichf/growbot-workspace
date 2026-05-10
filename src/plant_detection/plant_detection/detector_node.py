import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import os

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

        # Load YOLO model
        self.model = YOLO(
            os.path.expanduser("~/growbot-workspace/yolov8/runs/detect/yolov8_potted_plants-12/weights/best.pt")
        )

        self.get_logger().info("Plant detector node started.")

    def callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

        results = self.model(frame)

        annotated = results[0].plot()

        cv2.imshow("Plant Detection", annotated)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = PlantDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()