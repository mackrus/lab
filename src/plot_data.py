from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set a crisp style
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["font.family"] = "serif"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMAGES_DIR = ROOT / "images"
STARTUP_CUTOFF_S = 20.0
MASS_STABLE_WINDOW_S = 5.0
MAX_POWER_W = 250.0
MAX_POWER_STEP_W = 50.0
PLOT_POWER_YMAX_W = 200.0

# Uncertainty constants
ERR_TEMP_C = 0.1  # Sensor precision in Celsius
ERR_MASS_REL = 0.02  # 2% uncertainty in mass estimation
ERR_POWER_REL = 0.02  # 2% uncertainty in power (Capstone sensor spec)


def load_lab_csv(path, run_name=None):
    """
    Robustly load lab CSV data with semicolon delimiters and comma decimals.
    If run_name is provided, only loads columns associated with that run number (e.g., 'Run #5').
    """
    with open(path, "r", encoding="utf-8") as f:
        header_line = f.readline().strip()
        header = [h.strip('"') for h in header_line.split(";")]

    usecols = None

    if run_name:
        # Find all columns that match the run_name
        indices = [i for i, h in enumerate(header) if run_name in h]
        if not indices:
            raise ValueError(f"Run name '{run_name}' not found in {path}")

        # Check if the first column of the run is a 'Date and Time' string
        if "Date and Time" in header[indices[0]]:
            usecols = indices[1:]
        else:
            usecols = indices
    else:
        # Default behavior: take the first run block
        if "Date and Time" in header[0]:
            usecols = range(1, 8)  # Date, Time, 3xH, 3xC
        else:
            usecols = range(0, 7)

    def comma_converter(s):
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return np.nan

    converters = {i: comma_converter for i in range(len(header))}

    data = np.genfromtxt(
        path,
        delimiter=";",
        skip_header=1,
        converters=converters,
        usecols=usecols,
        encoding="utf-8",
    )
    return data


data_run_1 = load_lab_csv(DATA_DIR / "run_1_8_may.csv")
data_run_2 = load_lab_csv(DATA_DIR / "run_2_8_may.csv", run_name="Run #6")
data_run_3 = load_lab_csv(DATA_DIR / "run_3_8_may.csv")


def calculate_cop(data, m_h, m_c, t_power, p_power):
    """
    Calculate COP_H and COP_C based on temperature changes and actual compressor power.
    Includes uncertainty propagation for COP_H.
    """
    cp = 4180.0  # J/(kg*K)
    data = trim_startup(data)
    t = data[:, 0]
    th = data[:, 1]  # Reservoir T_H
    tc = data[:, 4]  # Reservoir T_C

    dt = np.gradient(t)
    dt[dt == 0] = np.nan
    dth = np.gradient(th) / dt
    dtc = np.gradient(tc) / dt

    # 30-second smoothing window at 20Hz
    window = 600
    dth_smooth = smooth_signal(dth, window=window)
    dtc_smooth = smooth_signal(dtc, window=window)

    q_h = m_h * cp * dth_smooth
    q_c = -m_c * cp * dtc_smooth

    # Interpolate power to match temperature timestamps
    p_interp = np.interp(t, t_power, p_power)
    # Smooth power with the same window to keep COP stable
    p_smooth = smooth_signal(p_interp, window=window)
    p_smooth = np.maximum(p_smooth, 1.0)  # Avoid division by zero

    cop_h = q_h / p_smooth
    cop_c = q_c / p_smooth
    delta_t = th - tc

    # Carnot COP = T_H (Kelvin) / Delta T
    # Avoid division by zero in case delta_t is very small
    th_k = th + 273.15
    cop_ideal = th_k / np.maximum(delta_t, 0.1)

    # Uncertainty propagation:
    # (dCOP/COP)^2 = (dm/m)^2 + (d(dT/dt)/(dT/dt))^2 + (dP/P)^2
    # For dT/dt, we estimate error as ERR_TEMP / delta_time_of_smoothing (30s)
    err_dt_dt = (ERR_TEMP_C / 30.0) / np.maximum(np.abs(dth_smooth), 1e-6)
    rel_err_sq = (ERR_MASS_REL) ** 2 + (err_dt_dt) ** 2 + (ERR_POWER_REL) ** 2
    err_h = np.abs(cop_h) * np.sqrt(rel_err_sq)

    return delta_t, cop_h, cop_c, cop_ideal, err_h


def load_power_csv(path):
    data = np.genfromtxt(
        path,
        delimiter=";",
        names=True,
        dtype=float,
        encoding="utf-8",
    )
    return data["t"], data["P_W"]


def trim_startup(data, cutoff_s=STARTUP_CUTOFF_S):
    mask = data[:, 0] >= cutoff_s
    return data[mask]


def trim_power_startup(t_power, p_power, cutoff_s=STARTUP_CUTOFF_S):
    mask = t_power >= cutoff_s
    return t_power[mask], p_power[mask]


def stable_mass_from_force(data, force_col=8, window_s=MASS_STABLE_WINDOW_S, g=9.82):
    t = data[:, 0]
    force = data[:, force_col]
    valid = np.isfinite(t) & np.isfinite(force)
    t_valid = t[valid]
    f_valid = force[valid]
    if len(t_valid) == 0:
        raise ValueError("No valid force samples found for mass estimation.")

    t_end = t_valid[-1]
    in_window = t_valid >= (t_end - window_s)
    f_stable = f_valid[in_window]
    if len(f_stable) == 0:
        raise ValueError(
            "No force samples found in stable end window for mass estimation."
        )

    # Use median of end window to suppress late noise/spikes.
    force_stable_n = float(np.nanmedian(f_stable))
    return force_stable_n / g


def smooth_signal(x, window=7):
    if window <= 1 or len(x) < window:
        return x
    kernel = np.ones(window, dtype=float) / window
    pad_w = window // 2
    x_padded = np.pad(x, (pad_w, window - 1 - pad_w), mode="edge")
    return np.convolve(x_padded, kernel, mode="valid")


def clean_power_signal(t_power, p_power):
    t_power = np.asarray(t_power, dtype=float)
    p_power = np.asarray(p_power, dtype=float)
    valid = np.isfinite(t_power) & np.isfinite(p_power)
    t = t_power[valid]
    p = p_power[valid].copy()
    if len(p) == 0:
        return t, p

    # Filter out unrealistic values (> MAX) and OCR zero-dropouts (< 50.0W)
    outlier = (p < 50.0) | (p > MAX_POWER_W)

    if len(p) >= 3:
        dp_prev = np.abs(p[1:-1] - p[:-2])
        dp_next = np.abs(p[1:-1] - p[2:])
        isolated_jump = (dp_prev > MAX_POWER_STEP_W) & (dp_next > MAX_POWER_STEP_W)
        outlier[1:-1] |= isolated_jump

    if np.any(outlier):
        keep = ~outlier
        if np.count_nonzero(keep) >= 2:
            p[outlier] = np.interp(t[outlier], t[keep], p[keep])
        else:
            p[outlier] = float(np.nanmedian(p))

    p = smooth_signal(p, window=7)
    return t, p


def main():

    g = 9.818  # Uppsala gravity constant
    bucket_n = 4.0

    # Run 1: Cold 48.86N, Hot 49.2N (minus bucket)
    run1_m_h = (49.2 - bucket_n) / g
    run1_m_c = (48.86 - bucket_n) / g

    # Run 2 & 3: Cold 48.5N, Hot 47.7N (minus bucket)
    run23_m_h = (47.7 - bucket_n) / g
    run23_m_c = (48.5 - bucket_n) / g

    print(
        "Med konstant massa för COP:"
        f" run1(m_h={run1_m_h:.3f}, m_c={run1_m_c:.3f}) kg,"
        f" run2/3(m_h={run23_m_h:.3f}, m_c={run23_m_c:.3f}) kg"
    )

    # Define color palettes (generate 4, drop the lightest, then reverse so index 0 is darkest)
    hot_colors = sns.color_palette("Reds", 4)[1:][::-1]
    cold_colors = sns.color_palette("Blues", 4)[1:][::-1]

    # 1. Temperature Plots (Individual Files)
    runs = [
        (data_run_1, "Mätning 1", DATA_DIR / "power_run_1.csv"),
        (data_run_2, "Mätning 2", DATA_DIR / "power_run_2.csv"),
        (data_run_3, "Mätning 3", DATA_DIR / "power_run_3.csv"),
    ]

    # Mapping based on thermodynamics:
    # Hot: T3 (Inlet Gas) > T1 (Reservoir) > T2 (Outlet Liquid)
    # Cold: T2 (Outlet Gas) > T1 (Reservoir) > T3 (Inlet Liquid)
    hot_labels = [
        "$T_H$ (Behållare)",
        "$T_H$ (Vätska ut)",
        "$T_H$ (Gas in)",
    ]
    cold_labels = [
        "$T_C$ (Behållare)",
        "$T_C$ (Gas ut)",
        "$T_C$ (Vätska in)",
    ]

    for i, (data, name, power_path) in enumerate(runs):
        fig, (ax, ax_p) = plt.subplots(
            2,
            1,
            figsize=(12, 8),
            sharex=True,
            gridspec_kw={"height_ratios": [4, 1], "hspace": 0.08},
        )

        # Select correct masses for the run
        mh = run1_m_h if i == 0 else run23_m_h
        mc = run1_m_c if i == 0 else run23_m_c

        data = trim_startup(data)
        t = data[:, 0]
        line_styles = ["-", "--", ":"]
        line_alphas = [1.0, 0.8, 0.8]

        # Hot channels (1-3)
        for i_ch in range(3):
            ax.plot(
                t,
                data[:, i_ch + 1],
                label=hot_labels[i_ch],
                color=hot_colors[i_ch],
                lw=2,
                linestyle=line_styles[i_ch],
                alpha=line_alphas[i_ch],
            )
        # Cold channels (4-6)
        for i_ch in range(3):
            ax.plot(
                t,
                data[:, i_ch + 4],
                label=cold_labels[i_ch],
                color=cold_colors[i_ch],
                lw=2,
                linestyle=line_styles[i_ch],
                alpha=line_alphas[i_ch],
            )

        t_power, p_power = load_power_csv(power_path)
        t_power, p_power = trim_power_startup(t_power, p_power)
        t_power, p_power = clean_power_signal(t_power, p_power)
        p_line = ax_p.plot(
            t_power,
            p_power,
            color="black",
            lw=1.8,
            alpha=0.65,
            label="$P(t)$",
        )[0]

        ax.set_title(
            f"{name}: Temperatur över tid ($m_H$={mh:.2f}kg, $m_C$={mc:.2f}kg)",
            pad=20,
        )
        ax.set_ylabel("Temperatur (°C)")
        ax_p.set_ylabel("Effekt (W)")
        ax_p.set_xlabel("Tid (s)")

        # Dynamic Y-axis for power to zoom in on the interesting range
        p_min, p_max = np.min(p_power), np.max(p_power)
        p_margin = (p_max - p_min) * 0.15 if p_max > p_min else 2.0
        ax_p.set_ylim(p_min - p_margin, p_max + p_margin)

        ax_p.grid(True, alpha=0.25)

        lines_1, labels_1 = ax.get_legend_handles_labels()
        ax.legend(
            lines_1,
            labels_1,
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
            borderaxespad=0.0,
        )
        ax_p.legend([p_line], ["$P(t)$"], loc="upper right")
        fig.tight_layout()

        filename = f"temperature_{name.lower().replace(' ', '')}.png"
        fig.savefig(IMAGES_DIR / filename, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"Plot saved to {filename}")

    # 2. COP Analysis
    def get_clean_power(path):
        t, p = load_power_csv(path)
        t, p = trim_power_startup(t, p)
        return clean_power_signal(t, p)

    t_p1, p_p1 = get_clean_power(DATA_DIR / "power_run_1.csv")
    dt1, coph1, copc1, id1, err1 = calculate_cop(
        data_run_1, run1_m_h, run1_m_c, t_p1, p_p1
    )

    t_p2, p_p2 = get_clean_power(DATA_DIR / "power_run_2.csv")
    dt2, coph2, copc2, id2, err2 = calculate_cop(
        data_run_2, run23_m_h, run23_m_c, t_p2, p_p2
    )

    t_p3, p_p3 = get_clean_power(DATA_DIR / "power_run_3.csv")
    dt3, coph3, copc3, id3, err3 = calculate_cop(
        data_run_3, run23_m_h, run23_m_c, t_p3, p_p3
    )

    plt.figure(figsize=(12, 7))
    mask1 = (dt1 > 1) & (dt1 < 35)
    mask2 = (dt2 > 1) & (dt2 < 35)
    mask3 = (dt3 > 1) & (dt3 < 40)

    run_colors = sns.color_palette("viridis", 3)

    # Plot Measured with Error Bands
    plt.plot(dt1[mask1], coph1[mask1], label="Mätserie 1", color=run_colors[0], lw=2.5)
    # plt.fill_between(dt1[mask1], coph1[mask1] - err1[mask1], coph1[mask1] + err1[mask1], color=run_colors[0], alpha=0.15)
    #
    plt.plot(dt2[mask2], coph2[mask2], label="Mätserie 2", color=run_colors[1], lw=2.5)
    # plt.fill_between(dt2[mask2], coph2[mask2] - err2[mask2], coph2[mask2] + err2[mask2], color=run_colors[1], alpha=0.15)
    #
    plt.plot(dt3[mask3], coph3[mask3], label="Mätserie 3", color=run_colors[2], lw=2.5)
    # plt.fill_between(dt3[mask3], coph3[mask3] - err3[mask3], coph3[mask3] + err3[mask3], color=run_colors[2], alpha=0.15)

    # Plot Ideal (Carnot) for each run
    plt.plot(
        dt1[mask1],
        id1[mask1],
        linestyle="--",
        color=run_colors[0],
        alpha=0.5,
        label="Mätserie 1: Ideal",
    )
    plt.plot(
        dt2[mask2],
        id2[mask2],
        linestyle="--",
        color=run_colors[1],
        alpha=0.5,
        label="Mätserie 2: Ideal",
    )
    plt.plot(
        dt3[mask3],
        id3[mask3],
        linestyle="--",
        color=run_colors[2],
        alpha=0.5,
        label="Mätserie 3: Ideal",
    )

    plt.title("COP vs Delta T: Uppmätt och idealt", pad=20)
    plt.xlabel("Delta T ($T_H - T_C$) [°C]")
    plt.ylabel("COP")
    plt.ylim(0, 20)
    plt.legend(ncol=2, fontsize="small")
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "cop_analysis.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("COP analysis saved to cop_analysis.png")


if __name__ == "__main__":
    main()
