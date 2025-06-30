#!/usr/bin/env python3

import argparse
from dvl_reader import DVLReader


def main():
    parser = argparse.ArgumentParser(description="Read DVL data (single or stream)")
    parser.add_argument(
        "--mode",
        choices=["single", "stream"],
        default="single",
        help="Choose between a one-time read or continuous stream",
    )
    args = parser.parse_args()

    reader = DVLReader()

    try:
        reader.setup()

        if args.mode == "single":
            result = reader.get_single()
            print("\n✅ Final Single Snapshot:")
            print(f"Roll:     {result['roll']:.2f}°")
            print(f"Pitch:    {result['pitch']:.2f}°")
            print(f"Yaw:      {result['yaw']:.2f}°")
            print(f"Depth:    {result['depth']:.2f} m")
            print(f"Altitude: {result['altitude']:.2f} m")
            print(f"FOM X:    {result['fom_x']:.2f}")
            print(f"FOM Y:    {result['fom_y']:.2f}")
            print(f"FOM Z:    {result['fom_z']:.2f}")
            print(f"B1:       {result['b1']:.2f} m")
            print(f"B2:       {result['b2']:.2f} m")
            print(f"B3:       {result['b3']:.2f} m")

        elif args.mode == "stream":
            reader.stream()

    finally:
        reader.stop()


if __name__ == "__main__":
    main()
