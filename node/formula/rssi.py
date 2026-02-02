"""
The RSSI formula is used to give the RSSI value a score.
"""

class RSSI:
    """
    RSSI class for handling radio signal strength indicator formula
    """
    def __init__(self, lower_bound: int, upper_bound: int, weight: float) -> None:
        RSSI.validate_bound(lower_bound)
        RSSI.validate_bound(upper_bound)
        RSSI.validate_weight(weight)

        self.weight      = weight
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.delta_bound = upper_bound - lower_bound

    @staticmethod
    def validate_bound(bound: int):
        """
        Ensure RSSI bound is set between 0 dbm and -130 dbm.

        Excellent: 0 to -60 dBm

        Good: -60 to -80 dBm

        Borderline: -90 to -100 dBm

        Poor: -110 to -120 dBm

        """
        if -130 < bound < 0:
            raise ValueError(f"{bound} dBm is not a valid value. RSSI values must be between 0 dBm and -130 dBm.")
    
    @staticmethod
    def validate_weight(weight: float):
        """
        Validate weight being set.

        Recommended value between 15% and 40%. Default value is 20%.

        Going above 40% may lead to unstable communications, as ETX is a more
        reliable method for measuring link reliability.
        """
        if not 0.0 < weight <= 1.0:
            raise ValueError(f"{weight*100}% is not a valid weight. Weight must be higher than 0 and lower than 1.")

    def get_score(self, rssi: int) -> float:
        """
        Validate RSSI exists between lower_bound and upper_bound.
        
        Return 1.0 if RSSI is greater than lower_bound,
        return 0.0 if RSSI is lower than upper_bound.

        Perform RSSI score formula and return the score.
        """
        if rssi >= self.lower_bound:
            return 1.0

        if rssi <= self.upper_bound:
            return 0.0

        return (rssi - self.lower_bound) / self.delta_bound

    @staticmethod
    def smooth_step(score: float):
        """
        If score is 1.0 or 0.0 return it, otherwise perform smooth step function and return it.
        """
        if score in {1.0, 0.0}:
            return score
        quality = (score ** 2) * (3 - 2 * score)
        return quality

    def get_cost(self, rssi: int) -> float:
        """
        Return the weighted cost of RSSI.
        """
        score   = self.get_score(rssi)
        quality = RSSI.smooth_step(score)

        return quality * self.weight
