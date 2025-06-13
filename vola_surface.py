from scipy.interpolate import RegularGridInterpolator
import numpy as np

from scipy.interpolate import RegularGridInterpolator
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class VolatilitySurface:
    #TODO Think about defining a sparse matrix-> for our purposes, i.e. parametrizing each slice it should be a bad idea
    
    def __init__(self, strikes: list, maturities: list, vol_matrix: list, extrapolate: bool = False, fill_value: float = np.nan):
        """
        Initialize the volatility surface with strike and maturity grids and corresponding volatilities.

        Parameters:
            strikes (list of float): Strike grid (must be sorted ascending).
            maturities (list of float): Maturity grid (must be sorted ascending).
            vol_matrix (list of list of float): 2D list of volatilities, shape (len(strikes), len(maturities)).
            extrapolate (bool): Whether to allow extrapolation outside the grid.
            fill_value (float): Value to use for extrapolation if enabled.
        """

        self._strikes_np = np.asarray(strikes, dtype=float)
        self._maturities_np = np.asarray(maturities, dtype=float)
        self._vols_np = np.asarray(vol_matrix, dtype=float)

        if self._vols_np.shape != (len(self._strikes_np), len(self._maturities_np)):
            raise ValueError(f"vol_matrix must have shape ({len(self._strikes_np)}, {len(self._maturities_np)})")

        self._interpolator = RegularGridInterpolator(
            (self._strikes_np, self._maturities_np),
            self._vols_np,
            method='linear',
            bounds_error=not extrapolate,
            fill_value=fill_value
        )

    @property
    def strikes(self):
        return self._strikes_np.tolist()

    @property
    def maturities(self):
        return self._maturities_np.tolist()

    @property
    def vols(self):
        return self._vols_np.tolist()

    @property
    def numpy_grid(self):
        """
        Returns (strikes, maturities, vol_matrix) as NumPy arrays.
        """
        return self._strikes_np, self._maturities_np, self._vols_np

    def get_vol(self, strike: float, maturity: float) -> float:
        """
        Returns the interpolated volatility at a given strike and maturity.
        """
        return float(self._interpolator([[strike, maturity]]))

    def get_vol_grid(self, strikes_grid, maturities_grid):
        """
        Returns a 2D grid of interpolated vols for the provided strikes and maturities.
        """
        strikes_arr = np.asarray(strikes_grid)
        maturities_arr = np.asarray(maturities_grid)
        K, T = np.meshgrid(strikes_arr, maturities_arr, indexing='ij')
        points = np.column_stack([K.ravel(), T.ravel()])
        vols = self._interpolator(points)
        return vols.reshape(K.shape).tolist()

    def get_original_grid(self):
        """
        Returns the original grid of strikes, maturities, and the volatility matrix.
        """
        return self._strikes_np.tolist(), self._maturities_np.tolist(), self._vols_np.tolist()

    def get_original_grid_as_dataframe(self):
        """
        Returns the original grid as a pandas DataFrame (rows = strikes, columns = maturities).
        """
        return pd.DataFrame(self._vols_np, index=self._strikes_np, columns=self._maturities_np)

    def plot_surface(self, strikes_grid=None, maturities_grid=None, cmap='viridis'):
        """
        Plots the volatility surface as a 3D surface.
        """
        if strikes_grid is None:
            strikes_grid = self._strikes_np
        if maturities_grid is None:
            maturities_grid = self._maturities_np

        K, T = np.meshgrid(strikes_grid, maturities_grid, indexing='ij')
        Z = np.array(self.get_vol_grid(strikes_grid, maturities_grid))

        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(K, T, Z, cmap=cmap)
        ax.set_xlabel("Strike")
        ax.set_ylabel("Maturity")
        ax.set_zlabel("Volatility")
        plt.title("Volatility Surface")
        plt.tight_layout()
        plt.show()



if __name__ == "__main__":

    # Example surface
    strikes = [90, 100, 110, 120]
    maturities = [0.25, 0.5, 1.0]
    vol_matrix = [
        [0.30, 0.28, 0.25],
        [0.25, 0.23, 0.21],
        [0.28, 0.26, 0.24],
        [0.31, 0.29, 0.27],
    ]

    vol_surface = VolatilitySurface(strikes, maturities, vol_matrix)

    # Single query
    strike = 105
    maturity = 0.6
    interpolated_vol = vol_surface.get_vol(strike, maturity)
    print(f"Interpolated volatility at strike {strike}, maturity {maturity}: {interpolated_vol:.4f}")

    # Original grid
    strikes_grid, maturities_grid, vol_matrix_out = vol_surface.get_original_grid()
    print("Original strikes:", strikes_grid)
    print("Original maturities:", maturities_grid)
    print("Original volatility matrix:")
    for row in vol_matrix_out:
        print(row)

    # Original grid as DataFrame
    df = vol_surface.get_original_grid_as_dataframe()
    print("\nVol surface as DataFrame:")
    print(df)

    # Vol grid on new query grid
    strikes_query = [95, 100, 105, 115]
    maturities_query = [0.3, 0.6, 0.9]
    vol_grid = vol_surface.get_vol_grid(strikes_query, maturities_query)
    print("\nInterpolated vol grid:")
    for i, strike in enumerate(strikes_query):
        for j, maturity in enumerate(maturities_query):
            print(f"Strike {strike}, Maturity {maturity}: {vol_grid[i][j]:.4f}")
