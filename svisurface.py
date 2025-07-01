import numpy as np
import matplotlib.pyplot as plt
from enums import SVIParameterizationType
from svioptimizer import SVI


class SVISurface:
    def __init__(self, parameterization=SVIParameterizationType.RAW):
        self.parameterization = parameterization
        self.slices = {}  
        self.fitted_params = {} 

    def fit(self, market_data):
        """
        market_data_by_maturity: dict of {T: (k_array, iv_array)}
        """
        for T, (k, iv) in market_data.items():
            svi = SVI(self.parameterization)
            svi.optimize(k, iv)
            self.slices[T] = svi
            self.fitted_params[T] = svi.optimal_params

    def evaluate(self, k, T):

        if not self.fitted_params:
            raise RuntimeError("SVI surface has not been fitted yet.")

        maturities = sorted(self.slices.keys())

        # If T is exactly one of the fitted maturities, just return the slice value
        if T in self.slices:
            return self.slices[T].evaluate(k)

        # Otherwise find T1 < T < T2 for interpolation
        for i in range(len(maturities) - 1):
            T1 = maturities[i]
            T2 = maturities[i + 1]
            if T1 < T < T2:
                iv1 = self.slices[T1].evaluate(k)
                iv2 = self.slices[T2].evaluate(k)
                weight = (T - T1) / (T2 - T1)
                return (1 - weight) * iv1 + weight * iv2

        # Extrapolation: flat extrapolation outside known range
        if T < maturities[0]:
            return self.slices[maturities[0]].evaluate(k)
        if T > maturities[-1]:
            return self.slices[maturities[-1]].evaluate(k)


if __name__ == "__main__":
    # Example data: { maturity: ([strikes], [implied vols]) }
    data = {
        0.5: ([50, 75, 100, 125], [0.45, 0.32, 0.2, 0.16]),
        0.7: ([50, 75, 100, 125], [0.41, 0.32, 0.29, 0.25]),
        1.0: ([50, 75, 100, 125, 130], [0.5, 0.56, 0.69, 0.71, 0.8])
    }

    # Convert strike -> log-moneyness (assuming ATM at 100)
    spot = 100
    data_log_moneyness = {
        T: (np.log(np.array(k_array) / spot), np.array(iv_array))
        for T, (k_array, iv_array) in data.items()
    }

    # Fit SVI surface
    svi_surface = SVISurface(SVIParameterizationType.RAW)
    svi_surface.fit(data_log_moneyness)

    # Plot each maturity
    for T, (k, iv_market) in data_log_moneyness.items():
        iv_fit = svi_surface.evaluate(k, T)

        plt.figure(figsize=(8, 5))
        plt.scatter(k, iv_market, label="Market", color="blue", alpha=0.6)
        plt.plot(k, iv_fit, label="SVI Fit", color="red", linewidth=2)
        plt.xlabel("Log-Moneyness")
        plt.ylabel("Implied Volatility")
        plt.title(f"SVI Fit at Maturity {T}")
        plt.legend()
        plt.grid(True)
        plt.show()