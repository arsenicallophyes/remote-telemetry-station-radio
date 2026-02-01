from enum import Enum

class Band(str, Enum):

    # Europe
    EU433 = "EU433"
    EU863 = "EU863"

    # United States
    US902 = "US902"

    # Asia
    AS920 = "AS920"
    AS923 = "AS923"

    # Australia
    AU915 = "AU915"

    # India
    IN865 = "IN865"

    @classmethod
    def validate(cls, band: "Band") -> None:
        if band != cls.EU433 and band != cls.EU863:
            raise ValueError(f"Band {band.name} is disabled. Only EU433 and EU863 is supported at the moment.")
