"""
Define object node
"""
from time import monotonic

from node.transport.peer_table        import PeerTable

from node.storage.persistence_manager import PersistenceManager

from node.mac.band_airtime       import WaitTime
from node.mac.duty_cycle_tracker import DutyCycleTracker
from node.mac.channel_selection  import ChannelSelect

from node.mixins.commands import CommandsMixin
from node.mixins.radio    import RadioMixin
from node.mixins.utils    import UtilsMixin
from node.mixins.control  import ControlMixin
from node.mixins.data     import DataMixin
from node.mixins.etx      import EtxMixin

from node.protocol.parameters import CommandParameters, Parameters

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
class Node(RadioMixin, UtilsMixin, ControlMixin, DataMixin, EtxMixin, CommandsMixin):
    """
    Node class
    """
    time_scale: float = 4.0
    formula_weights: "Tuple[float, float]" = 0.3, 0.4
    temp: float = 0.5
    min_control_reserve_ratio: float = 0.20

    allow_wait_candidates: bool = True
    wait_horizon_sec: WaitTime  = WaitTime(15)
    listen_window: int          = 15

    control_band = BANDS[5] # Band P
    control_transmission_retries  = 5
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

    def main(self):
        deadline = monotonic() + self.listen_window

        while monotonic() < deadline:
            response = self.control_receive(deadline)

            if not response:
                continue

            parameters, source, peer = response

            now = monotonic()
            if not peer:
                if result:= parameters.get(CommandParameters.NETWORK_JOIN):
                    network_id = result
                    if network_id and isinstance(network_id, bytes):
                        self.network_accept(network_id, source)
                elif result:= parameters.get(CommandParameters.NETWORK_ACCEPT):
                    network_accept_sequence = result
                    if network_accept_sequence and isinstance(network_accept_sequence, int):
                        self.control_send_ack(source)
                else:
                    print(f"Unregistered peer: {source=}: {parameters}")
                return

            if parameters.get(CommandParameters.NETWORK_REJOIN):
                self.control_send_ack(source)
                self.network_join(self.listen_window, now)
            elif parameters.get(CommandParameters.START_ETX_TX):
                self.control_send_ack(source)
                self.start_etx(source, peer, tx_first=True)
            elif parameters.get(CommandParameters.START_ETX_RX):
                self.control_send_ack(source)
                self.start_etx(source, peer, tx_first=False)
            elif result:= parameters.get(CommandParameters.ETX_COUNT):
                successfully_transmitted_packets = result
                if not isinstance(successfully_transmitted_packets, int):
                    return
                self.etx_complete(peer, successfully_transmitted_packets)
            elif result:= parameters.get(Parameters.FREQUENCY_SWITCH):
                frequency, packet_time = result
                if not (isinstance(frequency, float) and isinstance(packet_time, float)):
                    return
                self.control_send_ack(source)
                self.data_receive(frequency, packet_time, now=now)
            else:
                return
