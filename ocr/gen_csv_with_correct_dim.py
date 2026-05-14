import pandas as pd
import numpy as np

def align_power_with_temp(temp_csv, ocr_csv, time_offset=0.0):
    # 1. Load and clean temperature data
    # (Handling the comma decimal separator found in your files)
    df_temp = pd.read_csv(temp_csv, sep=';')
    t_master = df_temp.iloc[:, 1].str.replace(',', '.').astype(float).values
    
    # 2. Load OCR power data
    df_ocr = pd.read_csv(ocr_csv)
    t_video = df_ocr['t'].values - time_offset
    p_video = df_ocr['P_W'].values
    
    # 3. Interpolate P onto the temperature time axis
    # This ensures len(P_aligned) == len(T)
    p_aligned = np.interp(t_master, t_video, p_video, left=0, right=p_video[-1])
    
    # 4. Add to dataframe
    df_temp['Power_W'] = p_aligned
    return df_temp

# Usage
# df_final = align_power_with_temp('data/run_1_8_may.csv', 'data/ocr_results_1.csv', time_offset=2.5)
# df_final.to_csv('data/combined_run_1.csv', index=False, sep=';')