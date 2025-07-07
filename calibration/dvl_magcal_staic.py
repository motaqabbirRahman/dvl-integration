#!/usr/bin/env python3

import time
from nucleus_driver import NucleusDriver

DVL_PORT = "/dev/ttyUSB1"  # Change to /dev/ttyUSB0 if needed


def run_magnetic_calibration():
    print(f"🧭 Starting Magnetic Field Calibration on {DVL_PORT}...")

    driver = NucleusDriver()
    driver.set_serial_configuration(DVL_PORT)
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
    run_magnetic_calibration()
