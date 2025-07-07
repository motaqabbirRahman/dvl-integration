
#!/usr/bin/env python3

from nucleus_driver import NucleusDriver
from enum import IntEnum
import time
import math


class DataID(IntEnum):
    AHRS = 0xD2
    ALTIMETER = 0xAA
    BOTTOM_TRACK = 0xB4


class DVLReader:
    def __init__(self, port="/dev/ttyUSB0"):
        self.port = port
        self.driver = NucleusDriver()
        self.ahrs_data = None
        self.altimeter_data = None
        self.bt_data = None

        self.x = 0.0
        self.y = 0.0
        self.total_distance = 0.0
        self.last_time = time.time()
        self.velocity_threshold = 0.01  # 1 cm/s noise floor

    def setup(self):
        self.driver.set_serial_configuration(self.port)
        self.driver.connect(connection_type="serial")
        self.driver.send_command('SETAHRS,DS="ON"\r\n')
        self.driver.send_command('SETALTI,DS="ON"\r\n')
        self.driver.send_command('SETBT,DS="ON"\r\n')
        self.driver.send_command('SETBT,MODE="CRAWLER"\r\n')
        self.driver.send_command("SAVE,CONFIG\r\n")
        self.driver.start_measurement()
        print("✅ DVL stream initialized. Position reset.")

    def stop(self):
        try:
            self.driver.stop()
        except Exception as e:
            print("Stop error:", e)
        self.driver.disconnect()

    def parse_packet(self, pkt):
        if pkt["id"] == DataID.AHRS:
            try:
                self.ahrs_data = {
                    "roll": pkt["ahrsData.roll"],
                    "pitch": pkt["ahrsData.pitch"],
                    "yaw": pkt["ahrsData.heading"],
                    "depth": pkt["depth"],
                }
            except KeyError as e:
                print("AHRS missing key:", e)

        elif pkt["id"] == DataID.ALTIMETER:
            try:
                self.altimeter_data = {
                    "altitude": pkt["altimeterDistance"]
                }
            except KeyError as e:
                print("Altimeter missing key:", e)

        elif pkt["id"] == DataID.BOTTOM_TRACK:
            try:
                self.bt_data = {
                    "fom_x": pkt["fomX"],
                    "fom_y": pkt["fomY"],
                    "fom_z": pkt["fomZ"],
                    "b1": pkt["distanceBeam1"],
                    "b2": pkt["distanceBeam2"],
                    "b3": pkt["distanceBeam3"],
                    "vx": pkt["velocityX"],
                    "vy": pkt["velocityY"],
                    "vz": pkt["velocityZ"],
                }
            except KeyError as e:
                print("Bottom Track missing key:", e)

    def stream(self):
        print("🔄 Streaming AHRS + Altimeter + Bottom Track... Press Ctrl-C to stop.")
        try:
            while True:
                pkt = self.driver.read_packet(timeout=2.0)
                if not pkt:
                    continue

                self.parse_packet(pkt)

                now = time.time()
                dt = now - self.last_time
                self.last_time = now

                if self.bt_data:
                    vx = self.bt_data["vx"]
                    vy = self.bt_data["vy"]
                    fom_x = self.bt_data["fom_x"]
                    fom_y = self.bt_data["fom_y"]

                    if fom_x > 1.5 or fom_y > 1.5:
                        print("⚠️ FOM too high — skipping integration")
                    elif abs(vx) < self.velocity_threshold and abs(vy) < self.velocity_threshold:
                        pass  # below noise threshold
                    else:
                        dx = vx * dt
                        dy = vy * dt
                        self.x += dx
                        self.y += dy
                        self.total_distance += math.sqrt(dx**2 + dy**2)

                # Print AHRS
                if self.ahrs_data:
                    print(
                        f"🎯 RPY: {self.ahrs_data['roll']}, "
                        f"{self.ahrs_data['pitch']}, "
                        f"{self.ahrs_data['yaw']} | "
                        f"Depth: {self.ahrs_data['depth']} m"
                    )

                # Print Altimeter
                if self.altimeter_data:
                    print(f"📏 Altimeter: {self.altimeter_data['altitude']} m")

                # Print Bottom Track
                if self.bt_data:
                    print(f"📶 FOM X: {self.bt_data['fom_x']} | Y: {self.bt_data['fom_y']}")
                    print(f"📡 B1: {self.bt_data['b1']} m | B2: {self.bt_data['b2']} m | B3: {self.bt_data['b3']} m")

                    drift = math.sqrt(self.x**2 + self.y**2)
                    print(f"📍 Distance Traveled: {self.total_distance} m | Drift from Start: {drift} m\n")

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n⏹️ Stream stopped by user.")


if __name__ == "__main__":
    reader = DVLReader()
    try:
        reader.setup()
        reader.stream()
    finally:
        reader.stop()

