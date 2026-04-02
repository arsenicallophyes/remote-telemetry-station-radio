"""
Define object node
"""
from node.transport.peer_table        import PeerTable
from node.storage.persistance_manager import PersistenceManager

from node.mac.band_airtime       import WaitTime
from node.mac.duty_cycle_tracker import DutyCycleTracker
from node.mac.channel_selection  import ChannelSelect

from node.mixins.radio   import RadioMixin
from node.mixins.utils   import UtilsMixin
from node.mixins.control import ControlMixin
from node.mixins.data    import DataMixin
from node.mixins.etx     import EtxMixin

from models.model            import SpreadingFactor, CodingRate
from regulations.types.model import BandsSeq
from regulations.EU863.bands import BANDS

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Tuple

# Adafruit RFM9X library does not support implicit
# header mode, thus spreading factor 6 is not supported.
# Spreading factor 6 requires an implicit header, as
# specified by the RFM95W Lora modem datasheet.
IMPLICIT_HEADER_MODE = False
ACK_MESSAGE = 1
NACK_IGNORE = "IGNORE"
class Node(RadioMixin, UtilsMixin, ControlMixin, DataMixin, EtxMixin):
    """
    Node class
    """
    time_scale: float = 4.0
    formula_weights: "Tuple[float, float]" = 0.3, 0.4
    temp: float = 0.5
    min_control_reserve_ratio: float = 0.20

    allow_wait_candidates: bool = True
    wait_horizon_sec: WaitTime = WaitTime(15)

    control_band = BANDS[5] # Band P
    control_transmition_retries = 5
    control_frequency = 869.8 # Must remain fixed and within control_band

    ack_wait = 0.5

    bandwidth = 125_000
    spreading_factor: "SpreadingFactor" = 7
    coding_rate: "CodingRate" = 5

    etx_packets_count = 20

    def __init__(self, name: str, node_id: int, freq: float, bands: BandsSeq) -> None:
        """
        Initialize class Node.

        :param name: Node's name
        :param node_id: Node's unique identifier
        """
        self.name      = name
        self.node_id   = node_id

        self.dc_tracker          = DutyCycleTracker()
        self.channels            = ChannelSelect(self.bandwidth)
        self.peer_table          = PeerTable()
        self.persistence_manager = PersistenceManager("/control", "/data")

        self.recovery     = None
        self.retransmit   = None

        self.__init_radio__(freq, bands)
        self.__init_rtc__()

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: object) -> bool:
        return value == self.name

    def __str__(self) -> str:
        return self.name
