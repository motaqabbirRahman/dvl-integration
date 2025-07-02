#!/usr/bin/env python3

from nucleus_driver import NucleusDriver


def test_magcal(port="/dev/ttyUSB1"):
    print(f"🔍 Connecting to DVL on {port}...")

    driver = NucleusDriver()
    driver.set_serial_configuration(port)
    driver.connect(connection_type="serial")

    print("✅ Connected.")
    print("🧭 AHRS Mode:", driver.send_command("GETAHRS,MODE\r\n").strip())
    print("📦 MAGCAL Offsets:", driver.send_command("GETMAGCAL\r\n").strip())

    driver.disconnect()
    print("✅ Disconnected.")


if __name__ == "__main__":
    test_magcal()
