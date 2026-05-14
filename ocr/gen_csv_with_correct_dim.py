import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def align_power_with_temp(temp_csv, ocr_csv, time_offset=0.0):
    # 1. Load and clean temperature data
    # (Handling the comma decimal separator found in your files)
    df_temp = pd.read_csv(temp_csv, sep=';')
    t_master = df_temp.iloc[:, 1].str.replace(',', '.').astype(float).values
    
    # 2. Load OCR power data
    df_ocr = pd.read_csv(ocr_csv, sep=';')
    t_video = df_ocr['t'].values - time_offset
    p_video = df_ocr['P_W'].values
    
    # 3. Interpolate P onto the temperature time axis
    # This ensures len(P_aligned) == len(T)
    p_aligned = np.interp(t_master, t_video, p_video, left=0, right=p_video[-1])
    
    # 4. Add to dataframe
    df_temp['Power_W'] = p_aligned
    return df_temp

def _default_output(temp_csv):
    p = Path(temp_csv)
    return p.with_name(f"{p.stem}_with_power.csv")


def main():
    parser = argparse.ArgumentParser(description="Align OCR power values with temperature timeline.")
    parser.add_argument("temp_csv", help="Temperature CSV path (semicolon-separated).")
    parser.add_argument("ocr_csv", help="OCR power CSV path (semicolon-separated).")
    parser.add_argument("-o", "--output", default=None, help="Output CSV path.")
    parser.add_argument("--time-offset", type=float, default=0.0, help="Offset in seconds.")
    args = parser.parse_args()

    output = Path(args.output) if args.output else _default_output(args.temp_csv)
    output.parent.mkdir(parents=True, exist_ok=True)

    df_final = align_power_with_temp(args.temp_csv, args.ocr_csv, time_offset=args.time_offset)
    df_final.to_csv(output, index=False, sep=';')
    print(f"Saved {len(df_final)} rows to {output.resolve()}")


if __name__ == "__main__":
    main()
