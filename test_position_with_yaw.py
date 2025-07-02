#!/usr/bin/env python3

import time
import math
from nucleus_driver import NucleusDriver
from enum import IntEnum


class DataID(IntEnum):
    AHRS = 0xD2
    BOTTOM_TRACK = 0xB4


class DVLWithYawEstimator:
    def __init__(self, port="/dev/ttyUSB1"):
        self.port = port
        self.driver = NucleusDriver()
        self.x = 0.0
        self.y = 0.0
        self.total_distance = 0.0
        self.last_time = None
        self.last_print_time = None
        self.last_yaw = None
        self.yaw = None
        self.vx = 0.0
        self.vy = 0.0
        self.fom_x = 0.0
        self.fom_y = 0.0

    def setup(self):
        self.driver.set_serial_configuration(self.port)
        self.driver.connect(connection_type="serial")
        self.driver.send_command('SETAHRS,DS="ON"\r\n')
        self.driver.send_command('SETBT,DS="ON"\r\n')
        self.driver.send_command('SETBT,MODE="CRAWLER"\r\n')
        self.driver.send_command("SAVE,CONFIG\r\n")
        self.driver.start_measurement()
        print("✅ DVL with yaw initialized and streaming...")

    def stop(self):
        self.driver.stop()
        self.driver.disconnect()
        print("\n🛑 DVL connection closed.")

    def update_position(self, dt):
        if self.yaw is None:
            return

        yaw_rad = math.radians(self.yaw)
        vx_ned = math.cos(yaw_rad) * self.vx - math.sin(yaw_rad) * self.vy
        vy_ned = math.sin(yaw_rad) * self.vx + math.cos(yaw_rad) * self.vy

        dx = vx_ned * dt
        dy = vy_ned * dt

        self.x += dx
        self.y += dy
        self.total_distance += math.sqrt(dx**2 + dy**2)

    def run(self):
        print("⏳ Starting position estimation with yaw correction...")
        self.last_time = time.time()
        self.last_print_time = time.time()

        try:
            while True:
                pkt = self.driver.read_packet(timeout=2.0)
                if not pkt:
                    continue

                now = time.time()
                dt = now - self.last_time
                self.last_time = now

                if pkt["id"] == DataID.BOTTOM_TRACK:
                    try:
                        self.vx = pkt["velocityX"]
                        self.vy = pkt["velocityY"]
                        self.fom_x = pkt.get("fomX", 1.0)
                        self.fom_y = pkt.get("fomY", 1.0)
                    except KeyError:
                        continue

                elif pkt["id"] == DataID.AHRS:
                    try:
                        self.last_yaw = self.yaw
                        self.yaw = pkt["ahrsData.heading"]
                    except KeyError:
                        continue

                # Only update position if yaw is valid
                if self.yaw is not None:
                    self.update_position(dt)

                # Print every 1 second
                if now - self.last_print_time > 1.0:
                    drift = math.sqrt(self.x**2 + self.y**2)
                    dx = self.x - getattr(self, "last_x", 0.0)
                    dy = self.y - getattr(self, "last_y", 0.0)

                    # 1. Main position and heading
                    print(
                        f"\n📍 Traveled X: {self.x:.2f} m | Y: {self.y:.2f} m | Yaw: {self.yaw:.1f}°"
                    )

                    # 2. Distance tracking
                    print(
                        f"🧭 Total Distance: {self.total_distance:.2f} m | Distance from Start: {drift:.2f} m"
                    )

                    # 3. HOMED check
                    if drift < 0.10:
                        print("✅ HOMED: You returned to the starting point!")

                    # 4. Optional warnings
                    if self.fom_x > 0.5 or self.fom_y > 0.5:
                        print("⚠️ FOM too high — Bottom Track may be unreliable!")

                    if self.last_yaw is not None:
                        yaw_jump = abs(self.yaw - self.last_yaw)
                        if yaw_jump > 45:
                            print(f"⚠️ Sudden yaw jump detected: Δ{yaw_jump:.1f}°")

                    # Save state for next cycle
                    self.last_print_time = now
                    self.last_x = self.x
                    self.last_y = self.y
                    self.last_yaw = self.yaw

                time.sleep(0.01)

        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    estimator = DVLWithYawEstimator(port="/dev/ttyUSB1")
    estimator.setup()
    estimator.run()
