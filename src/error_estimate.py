import numpy as np

from plot_data import load_lab_csv


def estimate_uncertainty_poly(data, m_h, m_c, p_pump=13.0, degree=3):
    """
    Estimate uncertainty in COP using polynomial fitting for derivatives.
    """
    dm = 0.05
    dp = 0.5
    cp = 4180.0

    t = data[:, 0]
    # Remove NaNs for fitting
    valid = ~np.isnan(np.nanmean(data[:, 1:4], axis=1))
    t = t[valid]
    th = np.nanmean(data[valid, 1:4], axis=1)
    tc = np.nanmean(data[valid, 4:7], axis=1)

    # Fit polynomials
    ph = np.polyfit(t, th, degree)
    pc = np.polyfit(t, tc, degree)

    # Derivative polynomials
    dph = np.polyder(ph)
    dpc = np.polyder(pc)

    # Evaluate derivatives
    dth_fit = np.polyval(dph, t)
    dtc_fit = np.polyval(dpc, t)

    # Estimate uncertainty in the fit derivative
    # This is complex, but as a heuristic, we can use the residual std dev
    res_h = np.std(th - np.polyval(ph, t))
    # Uncertainty in slope of a linear fit is s_y / (s_x * sqrt(N))
    # For higher order, it's similar. Let's use a conservative estimate.
    dt_range = t[-1] - t[0]
    ddt = res_h / (dt_range / np.sqrt(len(t)))

    q_h = m_h * cp * dth_fit
    q_c = -m_c * cp * dtc_fit

    cop_h = q_h / p_pump
    cop_c = q_c / p_pump

    rel_err_h = np.sqrt(
        (dm_rel) ** 2 + (ddt / np.abs(dth_fit)) ** 2 + (dp_rel) ** 2
    )

    return (
        np.polyval(ph, t) - np.polyval(pc, t),
        cop_h,
        cop_c,
        rel_err_h * np.abs(cop_h),
    )


def main():
    # Load data
    data_run_1 = load_lab_csv("../data/run_1_8_may.csv")

    # Masses from previous analysis
    g = 9.818  # Uppsala constant
    m_h = 32.25 / g
    m_c = 26.55 / g

    delta_t, cop_h, cop_c, err_h = estimate_uncertainty_poly(data_run_1, m_h, m_c)

    print(f"Polynomial Fit COP_H at start: {cop_h[0]:.2f} +/- {err_h[0]:.2f}")
    print(f"Polynomial Fit COP_H at end:   {cop_h[-1]:.2f} +/- {err_h[-1]:.2f}")
    print(f"Average Relative Error: {100 * np.nanmean(err_h / np.abs(cop_h)):.1f}%")


if __name__ == "__main__":
    main()
nanmean(err_h / np.abs(cop_h)):.1f}%")


if __name__ == "__main__":
    main()
