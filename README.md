# Nucleus DVL Data Streamer (`master.py`)

This script streams real-time data from a Nortek Nucleus1000 DVL via serial port, including:

- AHRS: roll, pitch, yaw, depth
- Altimeter: altitude from bottom
- Bottom Track: beam distances and FOM (Figure of Merit) data

---

## ✅ Requirements

- Python 3.8+
- Nortek `nucleus_driver` package (official or from GitHub)
- Access to the DVL device via `/dev/ttyUSB1` (or adjust port)

---

## 📦 Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv dvl-env
source dvl-env/bin/activate

pip install --upgrade pip
pip install pyserial

pip3 install nucleus_driver

# Clone and install the Nortek driver if not using pip:
git clone https://github.com/NortekSupport/nucleus_driver.git
cd nucleus_driver
pip install .
```

## 🔧 How to Calibrate

Run the calibration script:

```bash
python3 calibration/dvl_magcal.py
```

After Calibration verify with:

```bash
python3 calibration/test_magcal.py
```

Expected values :

```bash
🧭 AHRS Mode: AHRS.MODE = 0
📦 MAGCAL Offsets: AHRS.MAG_CAL = -0.12, 0.33, 0.08
```
