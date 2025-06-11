from enum import Enum, auto

class SVIParameterizationType(Enum):
    """
    Enum class to identify different SVI parameterizations.
    
    1. RAW: Original Gatheral formulation (5 parameters).
    2. NATURAL: Reparameterization using ATM variance and scaled moneyness.
    3. JUMP_WING: Market-intuitive version using wings and skew.
    """
    RAW = auto()           # a + b[ρ(k−m) + sqrt((k−m)^2 + σ²)]
    NATURAL = auto()       # (θ/2)[1 + ρφk + sqrt((φk+ρ)² + 1 − ρ²)]
    JUMP_WING = auto()     # (v, ψ, p, c, ṽ): ATM variance, skew, wing slopes

    def __str__(self):
        return self.name