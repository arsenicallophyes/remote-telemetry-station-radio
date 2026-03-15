import random

from models.model import Frequency
from exceptions.regulations.unknown_band_error import UnkownBandError

CHANNELS = {
    'K': {
        'Channels': [
            863.1, 863.3, 863.5, 863.7, 863.9, 864.1, 864.3, 864.5, 864.7, 864.9
            ]
        },
    'L': {
        'Channels': [
            865.1, 865.3, 865.5, 865.7, 865.9, 866.1, 866.3, 866.5, 866.7, 866.9,
            867.1, 867.3, 867.5, 867.7, 867.9,
            ]
        },
    'M': {
        'Channels': [
            868.1, 868.3, 868.5,
            ]
        },
    'N': {
        'Channels': [
            868.8, 869.0,
            ]
        },
    'O': {
        'Channels': [
            869.5,
            ]
        },
    'P': {
        'Channels': [
            869.8,
            ]
        },
    'Q': {
        'Channels': [
            869.8,
            ]
        }
 }
class ChannelSelect:

    def __init__(self, bandwidth: float) -> None:
        if bandwidth != 125.0:
            raise NotImplementedError(
                "Only a bandwidth of 125kHz is supported. "
                f"Provided {bandwidth=}"
            )
        self.bandwidth = bandwidth
        self.space = 200.0

    def select_channel(self, band_name: str) -> Frequency:
        """
        Random channel selected for the current implementation
        """
        channels = CHANNELS.get(band_name, {}).get("Channels")

        if channels is None:
            raise UnkownBandError(band_name, tuple(CHANNELS.keys()))

        index = random.randint(0, len(channels) - 1)

        return Frequency(channels[index])

    # def split(self):
    #     channels = {b.name: {"Channels": []} for b in BANDS}

    #     for b in BANDS:
    #         start = int((b.start + 0.100) * 1000)
    #         end = int(b.end * 1000)
    #         for i in range(start, end + 1, 200):
    #             centre_freq = i/1000
    #             if centre_freq != end / 1000:
    #                 channels[b.name]["Channels"].append(centre_freq)
