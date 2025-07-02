#!/usr/bin/env python3

import time
import argparse
import serial
from serial.tools import list_ports
from nucleus_driver import NucleusDriver


def get_available_usb_ports():
    return [p.device for p in list_ports.comports() if "USB" in p.device]


def detect_nortek_dvl_port():
    print("🔎 Scanning for Nortek DVL on USB ports...")
    for port in get_available_usb_ports():
        try:
            with serial.Serial(port, baudrate=115200, timeout=1) as ser:
                ser.write(b"GETVERSION\r\n")
                response = ser.read(100).decode(errors="ignore")
                if "VERSION" in response or "Nortek" in response:
                    print(f"✅ DVL detected on {port}")
                    return port
        except Exception:
            continue
    raise RuntimeError("❌ No Nortek DVL found on any USB port.")


def run_magnetic_calibration(port=None):
    if not port:
        port = detect_nortek_dvl_port()
    print(f"🧭 Starting Magnetic Field Calibration on {port}...")

    driver = NucleusDriver()
    driver.set_serial_configuration(port)
    driver.connect(connection_type="serial")

    print("✅ Connected to DVL")

    driver.send_command("SETAHRS,MODE=1\r\n")
    driver.send_command("SETFIELDCAL,MODE=1\r\n")
    driver.send_command("FIELDCAL\r\n")

    print(
        "🔄 Calibration started — rotate the AUV in all directions (roll, pitch, yaw)..."
    )

    try:
        start = time.time()
        while time.time() - start < 60:
            print(f"⏱️  Elapsed: {int(time.time() - start)}s", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔ Stopping early due to Ctrl+C.")

    print("\n🛑 Stopping calibration...")
    driver.send_command("STOP\r\n")

    print("💾 Saving MAGCAL...")
    driver.send_command("SAVE,MAGCAL\r\n")

    print("📦 Final calibration values:")
    print(driver.send_command("GETMAGCAL\r\n"))

    print("✅ Magnetic calibration complete.")
    driver.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DVL magnetic calibration")
    parser.add_argument("--port", type=str, help="Serial port (e.g. /dev/ttyUSB0)")
    args = parser.parse_args()

    run_magnetic_calibration(port=args.port)
