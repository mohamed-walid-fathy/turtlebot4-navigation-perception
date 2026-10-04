import rclpy
from rclpy.node import Node

from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import TwistStamped

import cv2
import numpy as np
import time
import os


class ApproachTwoColorsSpeech(Node):
    def __init__(self):
        super().__init__('approach_two_colors_speech')

        self.image_width = 250
        self.current_color = "UNKNOWN"
        self.target_x = None
        self.target_pixels = 0

        # Colors not yet visited
        self.remaining_colors = ["BLUE", "RED"]

        # Detection threshold
        self.MIN_PIXELS = 20

        # Stop distance threshold
        self.CLOSE_PIXELS = 3000

        self.image_sub = self.create_subscription(
            CompressedImage,
            '/oakd/rgb/preview/image_raw/compressed',
            self.image_callback,
            10
        )

        self.cmd_pub = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )

        self.get_logger().info("Approach BLUE and RED in any order started")

    def image_callback(self, msg):
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        self.image_width = frame.shape[1]

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        red_mask_1 = cv2.inRange(
            hsv,
            np.array([0, 50, 50]),
            np.array([15, 255, 255])
        )

        red_mask_2 = cv2.inRange(
            hsv,
            np.array([160, 50, 50]),
            np.array([180, 255, 255])
        )

        red_mask = red_mask_1 + red_mask_2

        blue_mask = cv2.inRange(
            hsv,
            np.array([90, 50, 40]),
            np.array([140, 255, 255])
        )

        red_pixels = cv2.countNonZero(red_mask)
        blue_pixels = cv2.countNonZero(blue_mask)

        self.current_color = "UNKNOWN"
        self.target_x = None
        self.target_pixels = 0

        best_color = None
        best_pixels = 0
        best_mask = None

        if "BLUE" in self.remaining_colors and blue_pixels > best_pixels:
            best_color = "BLUE"
            best_pixels = blue_pixels
            best_mask = blue_mask

        if "RED" in self.remaining_colors and red_pixels > best_pixels:
            best_color = "RED"
            best_pixels = red_pixels
            best_mask = red_mask

        if best_color is not None and best_pixels > self.MIN_PIXELS:
            moments = cv2.moments(best_mask)

            if moments["m00"] > 0:
                self.current_color = best_color
                self.target_x = int(moments["m10"] / moments["m00"])
                self.target_pixels = best_pixels

    def publish_cmd(self, linear_x=0.0, angular_z=0.0):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = "base_link"
        cmd.twist.linear.x = linear_x
        cmd.twist.angular.z = angular_z
        self.cmd_pub.publish(cmd)

    def stop_robot(self):
        for _ in range(10):
            self.publish_cmd(0.0, 0.0)
            time.sleep(0.05)

    def say_color(self, color):
        if color == "BLUE":
            os.system('espeak -s 120 -v en+f3 "Blue"')
        elif color == "RED":
            os.system('espeak -s 120 -v en+f3 "Red"')

    def search_for_target(self):
        self.get_logger().info("Searching...")

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)

            if self.current_color != "UNKNOWN":
                self.stop_robot()
                self.get_logger().info(f"{self.current_color} found")
                return

            
            self.publish_cmd(0.0, 0.53)

    def approach_target(self):
        target = self.current_color

        self.get_logger().info(f"Approaching {target}")

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)

            if self.current_color != target or self.target_x is None:
                self.get_logger().info(f"Lost {target}, searching again")
                return

            center_x = self.image_width / 2
            error = self.target_x - center_x

            self.get_logger().info(
                f"{target}: x={self.target_x}, error={error:.1f}, pixels={self.target_pixels}"
            )

            # Rotate toward target
            if abs(error) > 20:
                angular_z = -0.004 * error

                if angular_z > 0.30:
                    angular_z = 0.30
                elif angular_z < -0.30:
                    angular_z = -0.30

                self.publish_cmd(0.0, angular_z)
                continue

            # Move forward
            if self.target_pixels < self.CLOSE_PIXELS:
                self.publish_cmd(0.05, 0.0)
                continue

            # Arrived
            self.stop_robot()
            self.get_logger().info(f"Reached {target}")

            self.say_color(target)

            if target in self.remaining_colors:
                self.remaining_colors.remove(target)

            return

    def run_task(self):
        while len(self.remaining_colors) > 0:

            self.search_for_target()

            target = self.current_color

            self.approach_target()

            self.stop_robot()
            self.get_logger().info(f"Stopped at {target} for 3 seconds")
            time.sleep(3)

        self.stop_robot()
        self.get_logger().info("Finished visiting both colors")


def main():
    rclpy.init()

    node = ApproachTwoColorsSpeech()

    try:
        node.run_task()
    except KeyboardInterrupt:
        node.stop_robot()

    node.destroy_node()

    try:
        rclpy.shutdown()
    except Exception:
        pass


if __name__ == "__main__":
    main()
