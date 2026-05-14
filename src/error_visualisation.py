from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from plot_data import load_lab_csv, trim_startup, load_power_csv, trim_power_startup, clean_power_signal

# Style setup
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["font.family"] = "serif"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMAGES_DIR = ROOT / "images"

# Constants for uncertainty (estimates)
ERR_TEMP_C = 0.1       # Sensor precision in Celsius
ERR_MASS_REL = 0.02    # 2% uncertainty in mass estimation (scale noise/calibration)
ERR_POWER_REL = 0.03   # 3% uncertainty in power (OCR jitter/sampling)
CP = 4180.0            # J/(kg*K)

def calculate_uncertainty(data, m_h, t_power, p_power):
    """
    Calculate COP_H and its propagated uncertainty.
    """
    data = trim_startup(data)
    t = data[:, 0]
    th = data[:, 1]
    
    dt = np.gradient(t)
    dt[dt == 0] = np.nan
    dth = np.gradient(th) / dt
    
    # 30s smoothing
    window = 600
    kernel = np.ones(window) / window
    pad_w = window // 2
    
    def smooth(x):
        padded = np.pad(x, (pad_w, window - 1 - pad_w), mode="edge")
        return np.convolve(padded, kernel, mode="valid")

    dth_smooth = smooth(dth)
    
    # Power synchronization
    p_interp = np.interp(t, t_power, p_power)
    p_smooth = smooth(p_interp)
    p_smooth = np.maximum(p_smooth, 1.0)

    # COP_H = (m * cp * dT/dt) / P
    cop_h = (m_h * CP * dth_smooth) / p_smooth
    
    # Error propagation: 
    # (dCOP/COP)^2 = (dm/m)^2 + (d(dT/dt)/(dT/dt))^2 + (dP/P)^2
    # For dT/dt, we estimate error as ERR_TEMP / delta_time_of_smoothing
    err_dt_dt = (ERR_TEMP_C / 30.0) / np.abs(dth_smooth + 1e-6)
    
    rel_err_sq = (ERR_MASS_REL)**2 + (err_dt_dt)**2 + (ERR_POWER_REL)**2
    abs_err = cop_h * np.sqrt(rel_err_sq)
    
    # Sensitivity analysis: contributions to variance
    total_var = rel_err_sq
    contrib_mass = (ERR_MASS_REL**2) / total_var
    contrib_temp = (err_dt_dt**2) / total_var
    contrib_power = (ERR_POWER_REL**2) / total_var
    
    return t, th, cop_h, abs_err, (contrib_mass, contrib_temp, contrib_power)

def main():
    g = 9.82
    bucket_n = 4.0
    
    # Run 1
    m1_h = (49.2 - bucket_n) / g
    
    # Run 2 & 3
    m23_h = (47.7 - bucket_n) / g

    runs = [
        ("Run 1", DATA_DIR / "run_1_8_may.csv", None, m1_h, "data/power_run_1.csv"),
        ("Run 2", DATA_DIR / "run_2_8_may.csv", "Run #6", m23_h, "data/power_run_2.csv"),
        ("Run 3", DATA_DIR / "run_3_8_may.csv", None, m23_h, "data/power_run_3.csv"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    
    summary_data = []

    for i, (name, path, r_name, m_h, p_path) in enumerate(runs):
        data = load_lab_csv(path, run_name=r_name)
        t_p, p_p = load_power_csv(p_path)
        t_p, p_p = trim_power_startup(t_p, p_p)
        t_p, p_p = clean_power_signal(t_p, p_p)
        
        t, th, cop, err, contribs = calculate_uncertainty(data, m_h, t_p, p_p)
        
        # Calculate relative error percentage
        rel_err_pct = np.nanmean(err / np.abs(cop + 1e-6)) * 100
        
        # Plot COP with error bands
        axes[i].plot(t, cop, label=f"{name} COP$_H$", color="darkred", lw=2)
        axes[i].fill_between(t, cop-err, cop+err, color="red", alpha=0.2, label=f"Error (~{rel_err_pct:.1f}%)")
        axes[i].legend(loc="upper right", fontsize='small')
        
        axes[i].set_title(f"{name} Uncertainty Analysis")
        axes[i].set_xlabel("Time (s)")
        axes[i].set_ylim(0, 10)
        if i == 0:
            axes[i].set_ylabel("COP$_H$")
        
        print(f"{name} Average Relative Error: {rel_err_pct:.1f}%")
        
        # Store average contributions for the bar chart
        summary_data.append({
            "name": name,
            "Mass": np.nanmean(contribs[0]),
            "Temp Grad": np.nanmean(contribs[1]),
            "Power": np.nanmean(contribs[2])
        })

    plt.tight_layout()
    fig.savefig(IMAGES_DIR / "uncertainty_cop_bands.png", dpi=300)
    print("Saved uncertainty_cop_bands.png")

    # Second Plot: Source of Error Comparison
    plt.figure(figsize=(10, 6))
    bottom = np.zeros(3)
    categories = ["Mass", "Temp Grad", "Power"]
    colors = ["#4C72B0", "#55A868", "#C44E52"]
    
    run_names = [s["name"] for s in summary_data]
    for cat_idx, cat in enumerate(categories):
        vals = [s[cat] for s in summary_data]
        plt.bar(run_names, vals, bottom=bottom, label=cat, color=colors[cat_idx], alpha=0.8)
        bottom += vals

    plt.title("Contribution to COP Uncertainty Variance")
    plt.ylabel("Fraction of Total Uncertainty")
    plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1))
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "error_sources_comparison.png", dpi=300)
    print("Saved error_sources_comparison.png")

if __name__ == "__main__":
    main()
