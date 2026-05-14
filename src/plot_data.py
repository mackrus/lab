import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

# Set a crisp style
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["font.family"] = "serif"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMAGES_DIR = ROOT / "images"
STARTUP_CUTOFF_S = 20.0
MASS_STABLE_WINDOW_S = 5.0
MAX_POWER_W = 1200.0
MAX_POWER_STEP_W = 120.0
PLOT_POWER_YMAX_W = 20.0


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


def calculate_cop(data, m_h, m_c, p_pump=13.0):
    """
    Calculate COP_H and COP_C based on temperature changes.
    """
    cp = 4180.0  # J/(kg*K)
    t = data[:, 0]
    th = np.nanmean(data[:, 1:4], axis=1)
    tc = np.nanmean(data[:, 4:7], axis=1)

    dt = np.gradient(t)
    dt[dt == 0] = np.nan
    dth = np.gradient(th) / dt
    dtc = np.gradient(tc) / dt

    window = 100
    dth_smooth = np.convolve(dth, np.ones(window) / window, mode="same")
    dtc_smooth = np.convolve(dtc, np.ones(window) / window, mode="same")

    q_h = m_h * cp * dth_smooth
    q_c = -m_c * cp * dtc_smooth

    cop_h = q_h / p_pump
    cop_c = q_c / p_pump
    delta_t = th - tc

    return delta_t, cop_h, cop_c


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
        raise ValueError("No force samples found in stable end window for mass estimation.")

    # Use median of end window to suppress late noise/spikes.
    force_stable_n = float(np.nanmedian(f_stable))
    return force_stable_n / g


def smooth_signal(x, window=7):
    if window <= 1 or len(x) < window:
        return x
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(x, kernel, mode="same")


def clean_power_signal(t_power, p_power):
    t_power = np.asarray(t_power, dtype=float)
    p_power = np.asarray(p_power, dtype=float)
    valid = np.isfinite(t_power) & np.isfinite(p_power)
    t = t_power[valid]
    p = p_power[valid].copy()
    if len(p) == 0:
        return t, p

    outlier = (p < 0) | (p > MAX_POWER_W)

    if len(p) >= 3:
        dp_prev = np.abs(p[1:-1] - p[:-2])
        dp_next = np.abs(p[1:-1] - p[2:])
        isolated_jump = (dp_prev > MAX_POWER_STEP_W) & (dp_next > MAX_POWER_STEP_W)
        outlier[1:-1] |= isolated_jump

    med = float(np.nanmedian(p))
    mad = float(np.nanmedian(np.abs(p - med)))
    scale = 1.4826 * mad + 1e-9
    robust_z = np.abs((p - med) / scale)
    outlier |= robust_z > 8.0

    if np.any(outlier):
        keep = ~outlier
        if np.count_nonzero(keep) >= 2:
            p[outlier] = np.interp(t[outlier], t[keep], p[keep])
        else:
            p[outlier] = med

    p = smooth_signal(p, window=7)
    return t, p


def main():

    g = 9.82  # Uppsala gravity constant
    # Run 1 used a different fill target (from logged force values in error_estimate).
    run1_m_h = 32.25 / g
    run1_m_c = 26.55 / g

    raw_run_2 = load_lab_csv(DATA_DIR / "run_2_8_may.csv", run_name="Run #2")
    run23_m_h = stable_mass_from_force(
        raw_run_2, force_col=8, window_s=MASS_STABLE_WINDOW_S, g=g
    )
    raw_run_3_force = load_lab_csv(DATA_DIR / "run_2_8_may.csv", run_name="Run #3")
    run23_m_c = stable_mass_from_force(
        raw_run_3_force, force_col=8, window_s=MASS_STABLE_WINDOW_S, g=g
    )
    print(
        "Using constant masses for COP:"
        f" run1(m_h={run1_m_h:.3f}, m_c={run1_m_c:.3f}) kg,"
        f" run2/3(m_h={run23_m_h:.3f}, m_c={run23_m_c:.3f}) kg"
    )

    # Define color palettes (generate 4, drop the lightest, then reverse so index 0 is darkest)
    hot_colors = sns.color_palette("Reds", 4)[1:][::-1]
    cold_colors = sns.color_palette("Blues", 4)[1:][::-1]

    # 1. Temperature Plots (Individual Files)
    runs = [
        (data_run_1, "Run 1", DATA_DIR / "power_run_1.csv"),
        (data_run_2, "Run 2", DATA_DIR / "power_run_2.csv"),
        (data_run_3, "Run 3", DATA_DIR / "power_run_3.csv"),
    ]

    # Mapping based on thermodynamics:
    # Hot: T3 (Inlet Gas) > T1 (Reservoir) > T2 (Outlet Liquid)
    # Cold: T2 (Outlet Gas) > T1 (Reservoir) > T3 (Inlet Liquid)
    hot_labels = [
        "$T_H$ (Reservoir)",
        "$T_H$ (Outlet Liquid)",
        "$T_H$ (Inlet Gas)",
    ]
    cold_labels = [
        "$T_C$ (Reservoir)",
        "$T_C$ (Outlet Gas)",
        "$T_C$ (Inlet Liquid)",
    ]

    for data, name, power_path in runs:
        fig, (ax, ax_p) = plt.subplots(
            2,
            1,
            figsize=(12, 8),
            sharex=True,
            gridspec_kw={"height_ratios": [4, 1], "hspace": 0.08},
        )
        data = trim_startup(data)
        t = data[:, 0]
        line_styles = ["-", "--", ":"]
        line_alphas = [1.0, 0.8, 0.8]

        # Hot channels (1-3)
        for i in range(3):
            ax.plot(
                t,
                data[:, i + 1],
                label=hot_labels[i],
                color=hot_colors[i],
                lw=2,
                linestyle=line_styles[i],
                alpha=line_alphas[i],
            )
        # Cold channels (4-6)
        for i in range(3):
            ax.plot(
                t,
                data[:, i + 4],
                label=cold_labels[i],
                color=cold_colors[i],
                lw=2,
                linestyle=line_styles[i],
                alpha=line_alphas[i],
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

        ax.set_title(f"{name}: Temperature Evolution", pad=20)
        ax.set_ylabel("Temperature (°C)")
        ax_p.set_ylabel("Power (W)")
        ax_p.set_xlabel("Time (s)")
        ax_p.set_ylim(0.0, PLOT_POWER_YMAX_W)
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
        fig.savefig(IMAGES_DIR / filename, dpi=300)
        plt.close(fig)
        print(f"Plot saved to {filename}")

    # 2. COP Analysis
    dt1, coph1, copc1 = calculate_cop(data_run_1, run1_m_h, run1_m_c)
    dt2, coph2, copc2 = calculate_cop(data_run_2, run23_m_h, run23_m_c)
    dt3, coph3, copc3 = calculate_cop(data_run_3, run23_m_h, run23_m_c)

    plt.figure(figsize=(10, 6))
    mask1 = (dt1 > 1) & (dt1 < 35)
    mask2 = (dt2 > 1) & (dt2 < 35)
    mask3 = (dt3 > 1) & (dt3 < 35)

    run_colors = sns.color_palette("viridis", 3)

    plt.plot(dt1[mask1], coph1[mask1], label="Run 1: COP_H", color=run_colors[0], lw=2)
    plt.plot(dt2[mask2], coph2[mask2], label="Run 2: COP_H", color=run_colors[1], lw=2)
    plt.plot(dt3[mask3], coph3[mask3], label="Run 3: COP_H", color=run_colors[2], lw=2)

    delta_t_range = np.linspace(2, 35, 100)
    t_h_ref = delta_t_range + 20 + 273.15
    cop_ideal = t_h_ref / delta_t_range
    plt.plot(delta_t_range, cop_ideal, "k:", label="Ideal COP_H (T_C=20°C)", alpha=0.6)

    plt.title("COP vs Delta T", pad=20)
    plt.xlabel("Delta T (T_H - T_C) [°C]")
    plt.ylabel("COP")
    plt.ylim(0, 15)
    plt.legend()
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "cop_analysis.png", dpi=300)
    plt.close()
    print("COP analysis saved to cop_analysis.png")


if __name__ == "__main__":
    main()
