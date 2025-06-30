#!/usr/bin/env python3

from nucleus_driver import NucleusDriver
from enum import IntEnum


class DataID(IntEnum):
    AHRS = 0xD2
    ALTIMETER = 0xAA
    BOTTOM_TRACK = 0xB4


class DVLReader:
    def __init__(self, port="/dev/ttyUSB1"):
        self.port = port
        self.driver = NucleusDriver()
        self.ahrs_data = None
        self.altimeter_data = None
        self.bt_data = None

    def setup(self):
        self.driver.set_serial_configuration(self.port)
        self.driver.connect(connection_type="serial")
        self.driver.send_command('SETAHRS,DS="ON"\r\n')
        self.driver.send_command('SETALTI,DS="ON"\r\n')
        self.driver.send_command('SETBT,DS="ON"\r\n')  # Bottom Track
        self.driver.send_command("SAVE,CONFIG\r\n")
        self.driver.start_measurement()

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
                self.altimeter_data = {"altitude": pkt["altimeterDistance"]}
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
                }
            except KeyError as e:
                print("BT missing key:", e)

    def get_single(self):
        print("🔍 Waiting for one full set of AHRS + Altimeter + Bottom Track data...")
        while True:
            pkt = self.driver.read_packet(timeout=2.0)
            if not pkt:
                continue

            self.parse_packet(pkt)

            if self.ahrs_data and self.altimeter_data and self.bt_data:
                return {**self.ahrs_data, **self.altimeter_data, **self.bt_data}

    def stream(self):
        print("🔄 Streaming AHRS + Altimeter + Bottom Track... Press Ctrl-C to stop.")
        try:
            while True:
                pkt = self.driver.read_packet(timeout=2.0)
                if not pkt:
                    continue
                self.parse_packet(pkt)

                if self.ahrs_data:
                    print(
                        f"🎯 RPY: {self.ahrs_data['roll']:.2f}, "
                        f"{self.ahrs_data['pitch']:.2f}, "
                        f"{self.ahrs_data['yaw']:.2f} | "
                        f"Depth: {self.ahrs_data['depth']:.2f} m"
                    )

                if self.altimeter_data:
                    print(f"📏 Altimeter: {self.altimeter_data['altitude']:.2f} m")

                if self.bt_data:
                    print(f"📶 FOM X: {self.bt_data['fom_x']:.2f}")
                    print(f"📶 FOM Y: {self.bt_data['fom_y']:.2f}")
                    print(f"📶 FOM Z: {self.bt_data['fom_z']:.2f}")
                    print(f"📡 B1:     {self.bt_data['b1']:.2f} m")
                    print(f"📡 B2:     {self.bt_data['b2']:.2f} m")
                    print(f"📡 B3:     {self.bt_data['b3']:.2f} m")

        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user.")
