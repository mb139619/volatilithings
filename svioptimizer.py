import numpy as np
from scipy.optimize import minimize
from enums import SVIParameterizationType


class SVI:
    def __init__(self, parameterization, initial_params):
        """
        Initialize SVI model.

        Parameters:
        - initial_params: initial guess for SVI parameters (a, b, rho, m, sigma)
        """
        self.initial_params = initial_params
        self.optimal_params = None
        self.parameterization = parameterization

    def svi_total_variance(self, params, k):
        """
        Compute total implied variance w(k) at log-moneyness k.

        Parameters:
        - params: tuple/list of SVI parameters (a, b, rho, m, sigma)
        - k: scalar or array of log-moneyness values

        Returns:
        - total variance(s)
        """
        if self.parameterization == SVIParameterizationType.RAW:
            a, b, rho, m, sigma = params
            k = np.asarray(k)  

            return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))

    def svi_implied_vol(self, params, k):
        """
        Compute implied volatility at log-moneyness k.

        Parameters:
        - params: tuple/list of SVI parameters (a, b, rho, m, sigma)
        - k: scalar or array of log-moneyness values

        Returns:
        - implied vol(s)
        """
        w = self.svi_total_variance(params, k)
        return np.sqrt(np.maximum(w, 1e-10))  # numerical safeguard

    def _mse_loss(self, params, k_market, iv_market):
        """
        Compute mean squared error loss between market and model vols.
        """
        iv_pred = self.svi_implied_vol(params, k_market)
        return np.mean((iv_pred - iv_market) ** 2)

    def optimize(self, k_market, iv_market):
        """
        Optimize SVI parameters to fit market implied vols.

        Parameters:
        - k_market: array-like, log-moneyness points
        - iv_market: array-like, market implied vols

        Returns:
        - optimal_params: optimized SVI parameters
        """
        if self.parameterization == SVIParameterizationType.RAW:
            bounds = [
                (-1, 1),            # a
                (1e-5, 10),         # b
                (-0.999, 0.999),    # rho
                (-5, 5),            # m
                (1e-5, 5)           # sigma
            ]

        result = minimize(
            lambda p: self._mse_loss(p, k_market, iv_market),
            self.initial_params,
            bounds = bounds
        )

        self.optimal_params = result.x
        return self.optimal_params

    def evaluate(self, k):
        """
        Evaluate implied volatilities at given log-moneyness k using optimal params.

        Parameters:
        - k: scalar or array of log-moneyness values

        Returns:
        - implied vol(s)
        """
        if self.optimal_params is None:
            raise RuntimeError("You must call optimize() before evaluate().")

        return self.svi_implied_vol(self.optimal_params, k)
