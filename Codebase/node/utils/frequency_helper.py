"""
Verify the frequency selected falls within EU433 and EU863-870 for unlicensed usage.
Limits and channels imposed on LoRaWAN do not apply to this project, thus the full
spectrum of EU863-870 can be utilized

~~~~~~~~~~~   EU433   ~~~~~~~~~~
• Minimum frequency: 433.175 MHz
• Maximum frequency: 434.665 MHz
~~~~~~~~~   EU863-870   ~~~~~~~~
• Minimum frequency: 863.000 MHz
• Maximum frequency: 870.000 MHz
"""
from Codebase.exceptions.regulations.licensed_frequency_error import LicensedFrequencyError

class FrequencyHelper:
    """
    Validate set frequency falls within the unlicensed range of the band.
    """
    class Europe:
        @staticmethod
        def validate_eu863_870(frequency: float):
            """
            Verify the frequency set falls between 863.000 and 870.000 MHz.
            """
            if not 863.000 <= frequency <= 870.000:
                raise LicensedFrequencyError(frequency)

        @staticmethod
        def validate_eu433(frequency: float):
            """
            Verify the frequency set falls between 433.175 and 434.665 MHz.
            """
            if not 433.175 <= frequency <= 434.665:
                raise LicensedFrequencyError(frequency)
