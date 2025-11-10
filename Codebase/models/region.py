from enum import Enum

class Region(str, Enum):
    EU = "EU"
    US = "US"
    AS = "AS"
    AU = "AU"
    IN = "IN"
    KR = "KR"
    CN = "CN"
    RU = "RU"
    BR = "BR"

    @classmethod
    def validate(cls, region: "Region") -> None:
        if region != cls.EU:
            raise ValueError(f"Region {region.name} is disabled. Only EU is supported at the moment.")
