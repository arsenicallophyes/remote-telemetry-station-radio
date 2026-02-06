import math

from models.model import SpreadingFactor, CodingRate

class Airtime:

    @staticmethod
    def _symbol_time(bandwidth: float, sf: SpreadingFactor) -> float:
        return (2 ** sf) / bandwidth

    @staticmethod
    def _preamble_time(n: int, symbol_time: float) -> float:
        return (n + 4.25) * symbol_time

    @staticmethod
    def _payload_bits_term(pl_bytes: int) -> int:
        return 8 * pl_bytes

    @staticmethod
    def _sf_term(sf: SpreadingFactor) -> int:
        return 4 * sf

    @staticmethod
    def _crc_term(crc: bool) -> int:
        return 16 * crc

    @staticmethod
    def _ih_term(ih: bool) -> int:
        return 20 * ih

    @staticmethod
    def _payload_denominator(sf: SpreadingFactor, de: bool) -> int:
        return 4 * (sf - 2 * de)

    @staticmethod
    def _payload_numerator(pl_bytes: int, sf: SpreadingFactor, crc: bool, ih: bool) -> int:

        return (
            Airtime._payload_bits_term(pl_bytes) -
            Airtime._sf_term(sf) +
            28 +
            Airtime._crc_term(crc) -
            Airtime._ih_term(ih)
        )

    @staticmethod
    def _payload_symbol_blocks(numerator: int, denominator: int) -> int:
        return max(math.ceil(numerator/denominator), 0)

    @staticmethod
    def _payload_symbols(
        pl_bytes: int,
        sf: SpreadingFactor,
        ih: bool,
        de: bool,
        cr: CodingRate,
        crc: bool,
    ) -> int:
        """
        Calculate number of payload symbols.
        
        :param pl_bytes: Payload length in bytes.
        :type pl_bytes: int
        :param sf: Spreading factor
        :type sf: SpreadingFactor
        :param ih: True => implicit header mode (IH=1), False => explicit (IH=0).
        :type ih: bool
        :param de: Low data rate optimization enabled (DE=1)
        :type de: bool
        :param cr: Coding rate, 1 for 4/5 ... 4 for 4/8
        :type cr: CodingRate
        :param crc: True => CRC enabled.
        :type crc: bool
        :return: Number of payload symbols.
        :rtype: int
        """
        num = Airtime._payload_numerator(pl_bytes, sf, crc, ih)
        den = Airtime._payload_denominator(sf, de)
        blocks = Airtime._payload_symbol_blocks(num, den)
        return 8 + blocks * (cr + 4)

    @staticmethod
    def _packet_time(n_payload_symbols: int, t_sym: float, n_preamble: int) -> float:
        t_preamble = Airtime._preamble_time(n_preamble, t_sym)
        t_payload = n_payload_symbols * t_sym
        return t_payload + t_preamble

    @staticmethod
    def total_time(
        bandwidth: float,
        sf: SpreadingFactor,
        n_preamble: int,
        pl_bytes: int,
        ih: bool,
        de: bool,
        cr: CodingRate,
        crc: bool
    ) -> float:

        t_sym         = Airtime._symbol_time(bandwidth, sf)
        n_pay         = Airtime._payload_symbols(pl_bytes, sf, ih, de, cr, crc)
        packet_time   = Airtime._packet_time(n_pay, t_sym, n_preamble)

        return packet_time
