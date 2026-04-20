"""
Define object node
"""
from time import monotonic, sleep
import random

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

from node.protocol.parameters import CommandParameters, Parameters, add_timestamp, add_parameter

from models.model            import SpreadingFactor, CodingRate, Frequency
from models.packet           import Packet
from models.packet_type      import PacketKind

from regulations.types.model import BandsSeq
from regulations.EU863.bands import BANDS

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Tuple, Optional
    from node.base.routing_table import RoutingTable
    from models.model import NodeID, Message

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

    transmit_interval_sec = 30

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

        self.routing_table: "Optional[RoutingTable]" = None

        self.recovery     = None
        self.retransmit   = None

        self.boot         = False

        self._next_transmit = monotonic()

        self.__init_radio__(freq, bands)
        self.__init_rtc__()
    
    def install_routing_table(self, table: "RoutingTable") -> None:
        self.routing_table = table

    def startup(self):
        if self.boot:
            return
        print("Attemping to join network.")
        self.network_join(45)
        self.benchmark_all_nodes_with_etx()
        if self.peer_table.peers or self.node_id == 0:
            self.boot = True
        else:
            print("Failed to join network, sleeping.")
            sleep(15)

    def listen(self):
        deadline = monotonic() + self.listen_window * 3

        while monotonic() < deadline:
            response = self.control_receive(deadline)

            if not response:
                continue

            parameters, source, _, peer = response

            now = monotonic()
            if not peer:
                if result:= parameters.get(CommandParameters.NETWORK_JOIN):
                    print("NETWORK_JOIN")
                    network_id = result
                    if network_id and isinstance(network_id, bytes):
                        self.network_accept(network_id, source)
                        self._next_transmit = monotonic() + self.listen_window * 3

                elif result:= parameters.get(CommandParameters.NETWORK_ACCEPT):
                    print("NETWORK_ACCEPT")
                    network_accept_sequence = result
                    if network_accept_sequence and isinstance(network_accept_sequence, int):
                        self.control_send_ack(source)

                else:
                    print(f"Unregistered peer: {source=}: {parameters}")
                    print(response)
                return

            if parameters.get(CommandParameters.NETWORK_REJOIN):
                print("NETWORK_REJOIN")
                self.control_send_ack(source)
                self.network_join(self.listen_window, now)

            elif parameters.get(CommandParameters.START_ETX_TX):
                print("Start ETX TX")
                self.control_send_ack(source)
                self.start_etx(source, peer, tx_first=True)

            elif parameters.get(CommandParameters.START_ETX_RX):
                print("START ETX RX")
                self.control_send_ack(source)
                self.start_etx(source, peer, tx_first=False)

            elif result:= parameters.get(CommandParameters.ETX_COUNT):
                print("ETX Count")
                successfully_transmitted_packets = result
                if not isinstance(successfully_transmitted_packets, int):
                    return
                print("etx_complete")
                self.etx_complete(peer, successfully_transmitted_packets)

            elif result:= parameters.get(Parameters.FREQUENCY_SWITCH):
                print("Frequency Switch | data_receive")
                frequency, packet_time = result
                if not (isinstance(frequency, float) and isinstance(packet_time, float)):
                    return
                frequency = Frequency(frequency)
                self.control_send_ack(source)
                self.data_receive(frequency, packet_time, now=now)

                if self.recovery:
                    print("Initiating Data Recovery Mode | data_recovery")
                    self.data_recovery(self.listen_window)

            else:
                return

    def collect_sensors_data(self) -> str:
        #   Replace with importing sensor template, reading all sensor data
        words = (
            "Testing",
            "Infinite Chickens",
            "no",
            "Cows go moo",
            "LoRa sounds like a nice project, right? right??",
            "Behind you!",
            )

        index = random.randint(0, len(words) -1)
        return words[index]
    
    def _send_data_to_next_hop(
        self,
        next_hop_id: "NodeID",
        message: "Message",
        now: float,
        ):
        peer = self.peer_table.get_peer(next_hop_id)
        if not peer:
            print(f"Next hop ID {{{next_hop_id}}} is not registered.")
            return False

        packet = Packet(
            self.node_id,
            next_hop_id,
            PacketKind.DATA,
            peer.transmit.next_data_seq,
            message,
        )

        self.persistence_manager.store_packet(packet)

        return self.data_transmit(packet, now)

    def transmit_upstream(self, message: "Message", now: "Optional[float]" = None) -> bool:
        now = monotonic() if now is None else now

        if self.routing_table is None:
            print("Routing table not installed, transmission failed.")
            return False

        primary_id = self.routing_table.parent
        if primary_id is None:
            print("Routing table does not have a parent, transmission failed.")
            return False

        if self._send_data_to_next_hop(primary_id, message, now):
            return True

        backup_id = self.routing_table.backup_parent
        if backup_id is None:
            print(f"Primary {{{primary_id}}} is unresponsive, no backup set, transmission failed.")
            return False

        failover_message = add_parameter(message, Parameters.LINK_FAILURE, str(primary_id))

        if self._send_data_to_next_hop(backup_id, failover_message, now):
            print(f"Alternative routing via {{{backup_id}}} succeeded.")
            return True

        print(f"Alternative routing via {{{backup_id}}} failed, dropping packet, transmission failed.")
        return False

    def transmit(self, now: "Optional[float]"):
        now = monotonic() if now is None else now

        data = self.collect_sensors_data()

        message = add_parameter(None, Parameters.DATA, data)

        message = add_timestamp(self.rtc.datetime, message)

        self.transmit_upstream(message, now)

        if self.retransmit:
            self.data_retransmission()

        self._next_transmit = now + self.transmit_interval_sec

    def run(self):
        while not self.boot:
            self.startup()
        print("Startup Complete")
        if self.node_id != 0:
            print("Transmitting...")

        while True:
            now = monotonic()

            if self.node_id != 0:
                if self.peer_table.peers and now >= self._next_transmit:
                    print("Transmitting...")
                    self.transmit(now)
                    print("Listening...")

            self.listen()
