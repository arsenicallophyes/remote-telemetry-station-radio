"""
Define Expected Transmission Count formula class
"""

class ETX:
    """
    ETX class for handling expected transmission count formula
    """
    def __init__(self, weight: float) -> None:
        ETX.validate_weight(weight)

        self.weight = weight

    @staticmethod
    def validate_weight(weight: float):
        """
        Validate weight being set.

        Recommended value between 55% and 90%. Default value is 75%.

        Going below 55% may lead to unstable communications, as ETX is a more
        reliable method for measuring link reliability.
        """
        if not 0.0 < weight <= 1.0:
            raise ValueError(f"{weight*100}% is not a valid weight. Weight must be higher than 0 and lower than 1.")

    @staticmethod
    def calculate_etx(packets: int, recv_trans: int, forw_trans: int):
        """
        Calculate expected transmission count.
        """
        ETX.validate_packets_count(packets)
        ETX.validate_transmission_packets(packets, recv_trans)
        ETX.validate_transmission_packets(packets, forw_trans)

        dr = packets / recv_trans
        df = packets / forw_trans

        return 1 / (df * dr)

    @staticmethod
    def validate_packets_count(packets: int) -> None:
        """
        Ensure numbers of packets used to measure ETX at least 5.
        Recommended value between 10 and 20.
        """
        if packets <= 4:
            raise ValueError(f"{packets} is not valid. Number of packets must be 5 or higher.")

    @staticmethod
    def validate_transmission_packets(packets: int, packet_trans: int):
        if packet_trans > packets:
            raise ValueError(f"Number of {packet_trans=} is not valid. Number of packets retansmissted must not greater than {packets=}.")

    def get_cost(self, packets: int, recv_trans: int, forw_trans: int):
        """
        Return the weighted cost of ETX.
        """
        etx = ETX.calculate_etx(packets, recv_trans, forw_trans)
        return self.weight * etx
