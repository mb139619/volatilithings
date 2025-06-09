def linear_interpolator(x1, x2, y1, y2, x_new):
    """
    Perform linear interpolation between two points (x1, y1) and (x2, y2).
    
    :param x1: The x-coordinate of the first point
    :param x2: The x-coordinate of the second point
    :param y1: The y-coordinate (rate) at x1
    :param y2: The y-coordinate (rate) at x2
    :param x_new: The x-coordinate (time) at which to interpolate
    
    :return: The interpolated y-value at x_new
    """
    return y1 * ((x2 - x_new) / (x2 - x1)) + y2 * ((x_new - x1) / (x2 - x1))


def bilinear_interpolator(x1, x2, y1, y2, z11, z12, z21, z22, x, y):
    """
    Perform bilinear interpolation for value at (x, y)
    given values at surrounding grid points.
    """
    denom = (x2 - x1) * (y2 - y1)
    if denom == 0:
        raise ValueError("Invalid interpolation box with zero area")

    return (
        z11 * (x2 - x) * (y2 - y) +
        z21 * (x - x1) * (y2 - y) +
        z12 * (x2 - x) * (y - y1) +
        z22 * (x - x1) * (y - y1)
    ) / denom