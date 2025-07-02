#!/usr/bin/env python3

import time
import math
from nucleus_driver import NucleusDriver
from enum import IntEnum


class DataID(IntEnum):
    AHRS = 0xD2
    ALTIMETER = 0xAA
    BOTTOM_TRACK = 0xB4


class DVLNoYawEstimator:
    def __init__(self, port="/dev/ttyUSB1"):
        self.port = port
        self.driver = NucleusDriver()
        self.vx = 0.0
        self.vy = 0.0
        self.x = 0.0
        self.y = 0.0
        self.total_distance = 0.0
        self.last_time = None
        self.last_print_time = None

    def setup(self):
        self.driver.set_serial_configuration(self.port)
        self.driver.connect(connection_type="serial")
        # self.driver.send_command('SETBT,MODE="NAVIGATION"\r\n')   # Default mode (mid-speed ops)
        # self.driver.send_command('SETBT,MODE="CRAWLER"\r\n')      # Best for pools, slow AUV, <1 m/s
        # self.driver.send_command('SETBT,MODE="WATERTRACK"\r\n')   # Track particles in water column (no bottom lock)
        # self.driver.send_command('SETBT,MODE="ROVER"\r\n')        # Higher-speed ops, deeper range self.driver.send_command('SETBT,MODE="CRAWLER"\r\n')
        self.driver.send_command('SETBT,MODE="CRAWLER"\r\n')
        self.driver.send_command('SETBT,DS="ON"\r\n')
        self.driver.send_command("SAVE,CONFIG\r\n")
        self.driver.start_measurement()
        print("✅ DVL initialized for no-yaw position estimation.")

    def stop(self):
        self.driver.stop()
        self.driver.disconnect()
        print("\n🛑 DVL connection closed.")

    def integrate_velocity(self, vx, vy, dt):
        dx = vx * dt
        dy = vy * dt
        self.x += dx
        self.y += dy
        self.total_distance += math.sqrt(dx**2 + dy**2)

    def run(self):
        print("⏳ Starting DVL stream (no yaw)...")
        self.last_time = time.time()
        self.last_print_time = time.time()

        try:
            while True:
                pkt = self.driver.read_packet(timeout=2.0)
                if not pkt or pkt["id"] != DataID.BOTTOM_TRACK:
                    continue

                try:
                    vx = pkt["velocityX"]
                    vy = pkt["velocityY"]
                except KeyError:
                    continue

                now = time.time()
                dt = now - self.last_time
                self.last_time = now

                self.integrate_velocity(vx, vy, dt)

                # Print every 1 second
                if now - self.last_print_time > 1.0:
                    print(
                        f"🧭 Vx: {vx:.2f} m/s | Vy: {vy:.2f} m/s | "
                        f"X: {self.x:.2f} m | Y: {self.y:.2f} m | "
                        f"Total: {self.total_distance:.2f} m"
                    )
                    self.last_print_time = now

                time.sleep(0.01)  # slight delay to avoid overload

        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    estimator = DVLNoYawEstimator(port="/dev/ttyUSB1")
    estimator.setup()
    estimator.run()
