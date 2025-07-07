
#!/usr/bin/env python3

import time
import math
from nucleus_driver import NucleusDriver
from enum import IntEnum


class DataID(IntEnum):
    AHRS = 0xD2
    BOTTOM_TRACK = 0xB4


class DVLWithYawEstimator:
    def __init__(self, port="/dev/ttyUSB2"):
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
        self.velocity_threshold = 0.01  # m/s noise cutoff

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

        # Reject near-zero velocities
        if abs(self.vx) < self.velocity_threshold and abs(self.vy) < self.velocity_threshold:
            print("⚠️ Velocities too small — skipping")
            return

        yaw_rad = math.radians(self.yaw)
        vx_ned = math.cos(yaw_rad) * self.vx - math.sin(yaw_rad) * self.vy
        vy_ned = math.sin(yaw_rad) * self.vx + math.cos(yaw_rad) * self.vy

        dx = vx_ned * dt
        dy = vy_ned * dt

        self.x += dx
        self.y += dy
        self.total_distance += math.sqrt(dx ** 2 + dy ** 2)

    def run(self):
        print("⏳ Starting position estimation with yaw correction...")
        self.last_time = time.time()
        self.last_print_time = time.time()

        try:
            while True:
                pkt = self.driver.read_packet(timeout=3.0)
                if not pkt:
                    continue

                now = time.time()
                dt = now - self.last_time
                self.last_time = now

                print(f"[DEBUG] Packet received: ID={pkt.get('id')}")

                if pkt["id"] == DataID.BOTTOM_TRACK:
                    try:
                        self.vx = pkt["velocityX"]
                        self.vy = pkt["velocityY"]
                        self.fom_x = pkt.get("fomX", 2.0)
                        self.fom_y = pkt.get("fomY", 2.0)
                        status = pkt.get("status", 0)
                        valid_vx = (status & (1 << 9)) != 0
                        valid_vy = (status & (1 << 10)) != 0

                        print(f"[BT] vx: {self.vx} | vy: {self.vy} | fomX: {self.fom_x} | fomY: {self.fom_y} | status: {status} | valid_vx: {valid_vx} | valid_vy: {valid_vy}")

                        if not (valid_vx and valid_vy):
                            print("⚠️ Velocity status invalid — skipping")
                            self.vx = 0.0
                            self.vy = 0.0
                            continue

                    except KeyError:
                        print("⚠️ Missing velocity fields")
                        continue

                elif pkt["id"] == DataID.AHRS:
                    try:
                        self.last_yaw = self.yaw
                        self.yaw = pkt["ahrsData"]["heading"]
                        print(f"[AHRS] Yaw: {self.yaw}")
                    except KeyError:
                        print("⚠️ Missing AHRS heading")
                        continue

                if self.yaw is not None:
                    self.update_position(dt)

                if now - self.last_print_time > 2.0:
                    drift = math.sqrt(self.x ** 2 + self.y ** 2)
                    dx = self.x - getattr(self, "last_x", 0.0)
                    dy = self.y - getattr(self, "last_y", 0.0)

                    print(f"\n📍 X: {self.x} m | Y: {self.y} m | Yaw: {self.yaw}°")
                    print(f"🧭 Total Distance: {self.total_distance} m | Distance from Start: {drift} m")

                    if drift < 1:
                        print("✅ HOMED: You returned to the starting point!")

                    if self.fom_x > 1.5 or self.fom_y > 1.5:
                        print("⚠️ FOM too high — Bottom Track may be unreliable!")

                    if self.last_yaw is not None:
                        yaw_jump = abs(self.yaw - self.last_yaw)
                        if yaw_jump > 45:
                            print(f"⚠️ Sudden yaw jump detected: Δ{yaw_jump}°")

                    self.last_print_time = now
                    self.last_x = self.x
                    self.last_y = self.y
                    self.last_yaw = self.yaw

                time.sleep(0.01)

        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    estimator = DVLWithYawEstimator(port="/dev/ttyUSB2")
    estimator.setup()
    estimator.run()

