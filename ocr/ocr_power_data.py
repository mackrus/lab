import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pytesseract


def parse_power_value(raw_text, prev_value=None, max_power_w=160.0):
    s = "".join(ch for ch in raw_text if ch.isdigit() or ch == ".")
    if not s:
        return np.nan

    digits_only = s.replace(".", "")
    if not digits_only:
        return np.nan
        
    n = int(digits_only)
    candidates = [float(n), n / 10.0, n / 100.0]
    
    if len(digits_only) >= 3:
        frac = digits_only[3:] if len(digits_only) > 3 else "0"
        candidates.append(float(f"{digits_only[:3]}.{frac}"))
        
    valid = [c for c in candidates if 0.0 <= c <= max_power_w]
    if not valid:
        return np.nan

    active_candidates = [c for c in valid if 80.0 <= c <= max_power_w]
    
    if prev_value is not None and prev_value > 50.0:
        if active_candidates:
            return min(active_candidates, key=lambda x: abs(x - prev_value))
        return min(valid, key=lambda x: abs(x - prev_value))
    
    if active_candidates:
        # Compressor just turned on, jump to the most plausible active reading
        return max(active_candidates) 

    if prev_value is not None and np.isfinite(prev_value):
        return min(valid, key=lambda x: abs(x - prev_value))
        
    return max(valid)


def extract_power_to_csv(video_path, output_csv, sample_hz=1.0):
    video_path = Path(video_path).expanduser().resolve()
    output_csv = Path(output_csv).expanduser().resolve()
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        raise ValueError(f"Invalid FPS ({fps}) for video: {video_path}")

    data = []
    frame_count = 0

    # Configure Tesseract for 7-segment digits
    # --psm 7: Treat image as a single text line
    # whitelist: Only allow numbers and decimal points
    custom_config = r"--psm 7 -c tessedit_char_whitelist=0123456789."

    print(f"Processing {video_path}...")

    frame_step = max(1, int(round(fps / sample_hz)))
    prev_power = np.nan

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Since it's already BW and ROI, we just pass the frame to OCR
        # We sample at 1-second intervals (adjust if you need higher resolution)
        if frame_count % frame_step == 0:
            timestamp = frame_count / fps

            # Extract text
            raw_text = pytesseract.image_to_string(frame, config=custom_config).strip()

            p_val = parse_power_value(raw_text, prev_value=prev_power)
            if np.isfinite(p_val):
                prev_power = p_val

            data.append({"t": timestamp, "P_W": p_val})

        frame_count += 1

    cap.release()

    # Save to CSV
    df = pd.DataFrame(data, columns=["t", "P_W"])
    if not df.empty:
        # Clean up: interpolate missing values caused by OCR glitches
        df["P_W"] = df["P_W"].interpolate(limit_direction="both")
    df.to_csv(output_csv, index=False, sep=";")
    print(f"Saved {len(df)} rows to {output_csv}")


def _default_output_for_video(video_path):
    p = Path(video_path)
    return p.with_name(f"{p.stem}_power.csv")


def main():
    parser = argparse.ArgumentParser(
        description="Extract power values from a BW ROI video using OCR."
    )
    parser.add_argument(
        "video", nargs="?", default="run1_BW.mov", help="Path to input video."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to output CSV (default: <video_stem>_power.csv in same folder).",
    )
    parser.add_argument(
        "--sample-hz",
        type=float,
        default=1.0,
        help="Sampling frequency for OCR in Hz (default: 1.0).",
    )
    args = parser.parse_args()

    output = args.output or _default_output_for_video(args.video)
    extract_power_to_csv(args.video, output, sample_hz=args.sample_hz)


if __name__ == "__main__":
    main()
