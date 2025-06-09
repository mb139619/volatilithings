from utilities import bilinear_interpolator

class VolatilitySurface:
    """
    Represents a volatility surface defined over a grid of strikes and maturities,
    allowing bilinear interpolation to get volatility at any (strike, maturity) point.
    """

    def __init__(self, strikes: list, maturities: list, vol_matrix: list):
        """
        Initialize the volatility surface with strike and maturity grids and corresponding volatilities.

        Parameters:
            strikes (list of float): Strike grid (must be sorted ascending).
            maturities (list of float): Maturity grid (must be sorted ascending).
            vol_matrix (list of list of float): 2D list of volatilities, shape (len(strikes), len(maturities)).
        """
        self.strikes = strikes
        self.maturities = maturities
        self.vols = vol_matrix

        if len(self.vols) != len(self.strikes):
            raise ValueError(f"vol_matrix must have {len(self.strikes)} rows")
        for i, row in enumerate(self.vols):
            if len(row) != len(self.maturities):
                raise ValueError(f"Row {i} of vol_matrix must have {len(self.maturities)} columns")

    def get_vol(self, strike, maturity):
        """
        Returns the interpolated volatility at a given strike and maturity using bilinear interpolation.

        Parameters:
            strike (float): The strike to query.
            maturity (float): The maturity to query.

        Returns:
            float: Interpolated volatility.

        Raises:
            ValueError: If strike or maturity is out of bounds.
        """
        # Find strike bracket
        for i in range(1, len(self.strikes)):
            if self.strikes[i - 1] <= strike <= self.strikes[i]:
                ki = i - 1
                k1 = self.strikes[ki]
                k2 = self.strikes[ki + 1]
                break
        else:
            raise ValueError("Strike out of bounds")

        # Find maturity bracket
        for j in range(1, len(self.maturities)):
            if self.maturities[j - 1] <= maturity <= self.maturities[j]:
                tj = j - 1
                t1 = self.maturities[tj]
                t2 = self.maturities[tj + 1]
                break
        else:
            raise ValueError("Maturity out of bounds")

        # Fetch vols
        v11 = self.vols[ki][tj]
        v12 = self.vols[ki][tj + 1]
        v21 = self.vols[ki + 1][tj]
        v22 = self.vols[ki + 1][tj + 1]

        return bilinear_interpolator(k1, k2, t1, t2, v11, v12, v21, v22, strike, maturity)

    def get_original_grid(self):
        """
        Returns the original grid of strikes, maturities, and the volatility matrix.

        Returns:
            tuple: (strikes, maturities, vol_matrix)
        """
        return self.strikes, self.maturities, self.vols

    def get_original_grid_as_dataframe(self):
        """
        Returns the original grid as a pandas DataFrame (rows = strikes, columns = maturities).

        Returns:
            pandas.DataFrame: DataFrame with strikes as index and maturities as columns.
        """
        import pandas as pd
        return pd.DataFrame(self.vols, index=self.strikes, columns=self.maturities)

    def get_vol_grid(self, strikes_grid, maturities_grid):
        """
        Returns a 2D grid of interpolated vols for the provided strikes and maturities.

        Parameters:
            strikes_grid (list of float): Strikes to evaluate.
            maturities_grid (list of float): Maturities to evaluate.

        Returns:
            list of list of float: 2D list of interpolated vols. Each row corresponds to a strike,
                                   each column to a maturity.

        Raises:
            ValueError: If any query point is out of bounds.
        """
        vol_grid = []
        for strike in strikes_grid:
            vol_row = []
            for maturity in maturities_grid:
                vol = self.get_vol(strike, maturity)
                vol_row.append(vol)
            vol_grid.append(vol_row)
        return vol_grid


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
