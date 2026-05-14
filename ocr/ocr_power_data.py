import cv2
import numpy as np
import pandas as pd
import pytesseract


def extract_power_to_csv(video_path, output_csv):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    data = []
    frame_count = 0

    # Configure Tesseract for 7-segment digits
    # --psm 7: Treat image as a single text line
    # whitelist: Only allow numbers and decimal points
    custom_config = r"--psm 7 -c tessedit_char_whitelist=0123456789."

    print(f"Processing {video_path}...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Since it's already BW and ROI, we just pass the frame to OCR
        # We sample at 1-second intervals (adjust if you need higher resolution)
        if frame_count % int(fps) == 0:
            timestamp = frame_count / fps

            # Extract text
            raw_text = pytesseract.image_to_string(frame, config=custom_config).strip()

            try:
                p_val = float(raw_text)
            except ValueError:
                p_val = np.nan  # Handle misreads/glitches

            data.append({"t": timestamp, "P_W": p_val})

        frame_count += 1

    cap.release()

    # Save to CSV
    df = pd.DataFrame(data)
    # Clean up: Interpolate missing values caused by OCR glitches
    df["P_W"] = df["P_W"].interpolate()
    df.to_csv(output_csv, index=False, sep=";")
    print(f"Saved to {output_csv}")


# Usage
extract_power_to_csv("path/to/video_1.mov", "data/power_run_1.csv")

