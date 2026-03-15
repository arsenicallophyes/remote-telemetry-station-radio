from typing import Dict, Final

from regulations.EU863.bands import BANDS as EU863_BANDS
from regulations.types.model import BandsSeq

BAND_REGISTRY: Final[Dict[str, BandsSeq]] = {
    "EU863": EU863_BANDS
}

def get_bands(key: str) -> BandsSeq:
    try:
        return BAND_REGISTRY[key]
    except KeyError as e:
        raise ValueError(f"Band registery '{key}' is not enabled.") from e
