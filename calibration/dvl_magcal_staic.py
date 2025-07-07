
#!/usr/bin/env python3

import time
from nucleus_driver import NucleusDriver

DVL_PORT = "/dev/ttyUSB0"  # Change if needed


def check_calibration_flags(ahrs_status):
    """
    Bit 6 = soft iron
    Bit 7 = hard iron
    """
    soft_iron_calibrated = bool(ahrs_status & (1 << 6))
    hard_iron_calibrated = bool(ahrs_status & (1 << 7))

    print(f"\n📡 AHRS Calibration Flags:")
    print(f"  ➤ Soft Iron Calibrated: {'✅ Yes' if soft_iron_calibrated else '❌ No'}")
    print(f"  ➤ Hard Iron Calibrated: {'✅ Yes' if hard_iron_calibrated else '❌ No'}")

    return soft_iron_calibrated, hard_iron_calibrated


def run_magnetic_calibration():
    print(f"🧭 Starting Magnetic Field Calibration on {DVL_PORT}...")

    driver = NucleusDriver()
    driver.set_serial_configuration(DVL_PORT)
    driver.connect(connection_type="serial")
    print("✅ Connected to DVL")

    # Ensure AHRS is in mode that uses magnetometer
    driver.send_command("SETAHRS,MODE=1\r\n")

    # Begin magnetic calibration
    driver.send_command("SETFIELDCAL,MODE=1\r\n")
    driver.send_command("FIELDCAL\r\n")
    print("🔄 Calibration started — rotate the AUV slowly in all directions (roll, pitch, yaw)...")

    try:
        start = time.time()
        while time.time() - start < 60:
            print(f"⏱️  Elapsed: {int(time.time() - start)}s", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔ Stopping early due to Ctrl+C.")

    print("\n🛑 Stopping calibration...")
    driver.send_command("STOP\r\n")

    print("💾 Saving calibration...")
    driver.send_command("SAVE,MAGCAL\r\n")
    driver.send_command("SAVE,CONFIG\r\n")  # Ensures persistence

    print("📦 Fetching calibration values...")
    magcal_result = driver.send_command("GETMAGCAL\r\n")
    print(magcal_result)

    print("📦 Fetching AHRS status...")
    ahrs_status_result = driver.send_command("GET,AHRS\r\n")
    print(ahrs_status_result)

    # Parse AHRS status bits from response
    if "AHRS.STATUS" in ahrs_status_result:
        try:
            # Extract status value (e.g., "AHRS.STATUS=192")
            for line in ahrs_status_result.splitlines():
                if line.startswith("AHRS.STATUS="):
                    status_val = int(line.split("=")[1].strip())
                    check_calibration_flags(status_val)
                    break
        except Exception as e:
            print(f"⚠️ Could not parse AHRS.STATUS: {e}")
    else:
        print("⚠️ AHRS status field not found.")

    print("✅ Magnetic calibration complete.")
    driver.disconnect()


if __name__ == "__main__":
    run_magnetic_calibration()

