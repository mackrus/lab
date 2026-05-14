import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set a crisp style
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["font.family"] = "serif"


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


data_run_1 = load_lab_csv("../data/run_1_8_may.csv")
data_run_2 = load_lab_csv("../data/run_2_8_may.csv", run_name="Run #6")
data_run_3 = load_lab_csv("../data/run_3_8_may.csv")


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


def main():

    g = 9.82  # Uppsala gravity constant
    raw_run_2 = load_lab_csv("../data/run_2_8_may.csv", run_name="Run #2")
    m_h = np.nanmean(raw_run_2[:, 8]) / g
    raw_run_3_force = load_lab_csv("../data/run_2_8_may.csv", run_name="Run #3")
    m_c = np.nanmean(raw_run_3_force[:, 8]) / g

    # Define color palettes (generate 4, drop the lightest, then reverse so index 0 is darkest)
    hot_colors = sns.color_palette("Reds", 4)[1:][::-1]
    cold_colors = sns.color_palette("Blues", 4)[1:][::-1]

    # 1. Temperature Plots (Individual Files)
    runs = [
        (data_run_1, "Run 1"),
        (data_run_2, "Run 2"),
        (data_run_3, "Run 3"),
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

    for data, name in runs:
        plt.figure(figsize=(12, 7))
        t = data[:, 0]
        line_styles = ["-", "--", ":"]
        line_alphas = [1.0, 0.8, 0.8]

        # Hot channels (1-3)
        for i in range(3):
            plt.plot(
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
            plt.plot(
                t,
                data[:, i + 4],
                label=cold_labels[i],
                color=cold_colors[i],
                lw=2,
                linestyle=line_styles[i],
                alpha=line_alphas[i],
            )

        plt.title(f"{name}: Temperature Evolution", pad=20)
        plt.xlabel("Time (s)")
        plt.ylabel("Temperature (°C)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.0)
        plt.tight_layout()

        filename = f"temperature_{name.lower().replace(' ', '')}.png"
        plt.savefig(f"../images/{filename}", dpi=300)
        plt.close()
        print(f"Plot saved to {filename}")

    # 2. COP Analysis
    dt1, coph1, copc1 = calculate_cop(data_run_1, m_h, m_c)
    dt2, coph2, copc2 = calculate_cop(data_run_2, m_h, m_c)
    dt3, coph3, copc3 = calculate_cop(data_run_3, m_h, m_c)

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
    plt.savefig("../images/cop_analysis.png", dpi=300)
    plt.close()
    print("COP analysis saved to cop_analysis.png")


if __name__ == "__main__":
    main()
