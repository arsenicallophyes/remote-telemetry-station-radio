from math import exp
from random import uniform
from time import monotonic

from node.mac.band_airtime import BandAirtime
from node.mac.types.models import UsedTime, WaitTime

from models.packet_type import PacketKind, PacketKindType



try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Tuple, Optional, List, TypeAlias, Sequence, NewType
    Weight = NewType("Weight", float)
    BandsUsedTime: TypeAlias = List[Tuple[BandAirtime, UsedTime, WaitTime]]
    BandsWeights: TypeAlias = List[Tuple[BandAirtime, Weight, WaitTime]]
else:
    Weight = float
    BandsUsedTime = "List[Tuple[BandAirtime, UsedTime, WaitTime]]"
    BandsWeights = "List[Tuple[BandAirtime, Weight, WaitTime]]"

class BandSelect:

    @staticmethod
    def select_band(
            bands: "Sequence[BandAirtime]",
            packet_time: float,
            packet_type: "PacketKindType",
            time_scale: float,
            formula_weights: Tuple[float, float],
            temp: float,
            min_control_reserve_ratio: float,
            allow_wait_candidates: bool,
            wait_horizon_sec: WaitTime,
            now: "Optional[float]" = None,
        ) -> Tuple[BandAirtime, WaitTime]:
        if packet_type == PacketKind.CONTROL:
            return BandSelect.__control_packet_wait(bands, packet_time, now)

        return BandSelect.__data_packet_wait(
            bands,
            packet_time,
            time_scale,
            formula_weights,
            temp,
            min_control_reserve_ratio,
            allow_wait_candidates,
            wait_horizon_sec,
            now,
        )

    @staticmethod
    def __bands_wait_time(
            bands: "Sequence[BandAirtime]",
            packet_time: float,
            now: "Optional[float]" = None,
        ) -> "BandsUsedTime":

        bands_wait: "BandsUsedTime" = []
        for b in bands:
            used, wait = b.wait_until_legal(packet_time, now)
            bands_wait.append((b, used, wait))

        return bands_wait

    @staticmethod
    def __earliest_available(bands_wait: "BandsUsedTime") -> Tuple[BandAirtime, WaitTime]:
        band_airtime, _, wait = min(bands_wait, key= lambda x: x[2])
        return band_airtime, wait

    @staticmethod
    def __earliest_data_available(
            bands_wait: "BandsUsedTime",
            packet_time: float,
            min_control_reserve_ratio: float,
            now: "Optional[float]",
        ) -> Tuple[BandAirtime, WaitTime]:

        sorted_bands = sorted(bands_wait, key= lambda x: x[2])
        for b, used, wait in sorted_bands:
            if wait != 0:
                used = b.used_at(wait, now)
            if BandSelect.__reserve_control_budget(b, used, packet_time, min_control_reserve_ratio):
                return b, wait

        return sorted_bands[0][0], sorted_bands[0][2]

    @staticmethod
    def __control_packet_wait(
            bands: "Sequence[BandAirtime]",
            packet_time: float,
            now: "Optional[float]" = None,
        ) -> Tuple[BandAirtime, WaitTime]:
        now = monotonic() if now is None else now
        bands_wait = BandSelect.__bands_wait_time(bands, packet_time, now)
        return BandSelect.__earliest_available(bands_wait)

    
    @staticmethod
    def __data_packet_wait(
            bands: "Sequence[BandAirtime]",
            packet_time: float,
            time_scale: float,
            formula_weights: Tuple[float, float],
            temp: float,
            min_control_reserve_ratio: float,
            allow_wait_candidates: bool,
            wait_horizon_sec: WaitTime,
            now: "Optional[float]" = None,
    ) -> Tuple[BandAirtime, WaitTime]:

        if wait_horizon_sec < 0:
            raise ValueError(f"Wait horzin seconds must be above 0, provided {wait_horizon_sec=}")

        if temp <= 0:
            raise ValueError(f"Temp must be above 0, provided {temp=}")

        if time_scale <= 0:
            raise ValueError(f"Time scale must be above 0, provided {time_scale=}")
        now = monotonic() if now is None else now
        bands_wait = BandSelect.__bands_wait_time(bands, packet_time, now)
        eligible_bands = BandSelect.__predict_control_headroom_at_send(
            bands_wait,
            allow_wait_candidates,
            wait_horizon_sec,
            packet_time,
            min_control_reserve_ratio,
            now,
        )
        if eligible_bands is None or len(eligible_bands) == 0:
            return BandSelect.__earliest_data_available(
                bands_wait,
                packet_time,
                min_control_reserve_ratio,
                now,
            )

        bands_score = BandSelect.__score_bands(
            eligible_bands,
            packet_time,
            time_scale,
            formula_weights,
        )

        bands_weight, weights_sum = BandSelect.__bands_weights(
            bands_score,
            temp,
            eligible_bands
        )

        if weights_sum <= 0:
            return BandSelect.__earliest_data_available(
                bands_wait,
                packet_time,
                min_control_reserve_ratio,
                now,
            )

        band, wait = BandSelect.__random_select(bands_weight, weights_sum)

        return band, wait

    @staticmethod
    def __filter_by_wait(
            bands_wait: "BandsUsedTime",
            allow_wait_candidates: bool,
            wait_horizon_sec: WaitTime
        ) -> "Optional[BandsUsedTime]":
        zero_wait = [x for x in bands_wait if x[2] == 0]
        if zero_wait:
            if allow_wait_candidates:
                return zero_wait
            return [x for x in bands_wait if x[2] <= wait_horizon_sec]
        return None

    @staticmethod
    def __predict_control_headroom_at_send(
            bands_wait: "BandsUsedTime",
            allow_wait_candidates: bool,
            wait_horizon_sec: WaitTime,
            packet_time: float,
            min_control_reserve_ratio: float,
            now: "Optional[float]",
        ) -> "Optional[BandsUsedTime]":

        filterd_bands = BandSelect.__filter_by_wait(
            bands_wait,
            allow_wait_candidates,
            wait_horizon_sec,
        )

        if filterd_bands is None or len(filterd_bands) == 0:
            return None

        eligible_bands: "BandsUsedTime" = []

        for b, used, wait in filterd_bands:

            band = BandSelect.__filter_band(
                b,
                used,
                wait,
                packet_time,
                min_control_reserve_ratio,
                now,
            )

            if band is not None:
                eligible_bands.append(band)

        return eligible_bands

    @staticmethod
    def __filter_band(
            band_airtime: BandAirtime,
            used: UsedTime,
            wait: WaitTime,
            packet_time: float,
            min_control_reserve_ratio: float,
            now: "Optional[float]",
        ) -> "Optional[Tuple[BandAirtime, UsedTime, WaitTime]]":

        if wait != 0:
            used = band_airtime.used_at(wait, now)

        if not BandSelect.__reserve_control_budget(
            band_airtime,
            used,
            packet_time,
            min_control_reserve_ratio,
        ):
            return None


        return band_airtime, used, wait

    @staticmethod
    def __reserve_control_budget(
            band_airtime: BandAirtime,
            used: UsedTime,
            packet_time: float,
            min_control_reserve_ratio: float,
        ) -> bool:

        B = band_airtime.hourly_budget # Hourly budget
        K = B - used                   # Budget remaining
        R = (K - packet_time) / B      # Remaining-after budget ratio


        # Reserve airtime for control packets
        return R >= min_control_reserve_ratio

    @staticmethod
    def __random_select(
            bands_score: "BandsWeights",
            weights_sum: float,
        ) -> Tuple[BandAirtime, WaitTime]:

        r = uniform(0, weights_sum)
        cumulative: float = 0.0

        for b, w, wait in bands_score:
            cumulative += w
            if r < cumulative:
                return b, wait

        band_airtime, _, wait = bands_score[-1]
        return band_airtime, wait

    @staticmethod
    def __score_bands(
            eligible_bands :"BandsUsedTime",
            packet_time: float,
            time_scale: float,
            formula_weights: Tuple[float, float],
        ) -> List[float]:

        w1, w2 = formula_weights
        scores: List[float] = []

        for b, used, wait in eligible_bands:
            U = (used + packet_time) / b.hourly_budget # Future utilization ratio
            T = wait / time_scale                      # Time wait penalty

            score = (
              - w1 * U # Avoid hotspots
              - w2 * T # Avoid waiting
            )
            scores.append(score)

        return scores
    
    @staticmethod
    def __bands_weights(
            scores: List[float],
            temp: float,
            eligible_bands: "BandsUsedTime",
        ) -> Tuple["BandsWeights", float]:

        bands_weight: "BandsWeights" = []
        m = max(scores)
        weights_sum = 0

        # Subtract max score to prevent computing large numbers on embedded devices
        # Probability remains constant

        for i, score in enumerate(scores):
            w = exp((score - m) / temp)
            weights_sum += w
            band = eligible_bands[i][0]
            wait = eligible_bands[i][2]
            bands_weight.append((band, Weight(w), wait))

        return bands_weight, weights_sum
