from time import monotonic, sleep

from models.packet import Packet
from models.packet_type import PacketKind
from models.model import NodeID

from node.protocol.parameters import CommandParameters, add_parameter, add_timestamp

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False  # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional
    from rtc import RTC # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-error
    from adafruit_rfm9x_patched import RFM9x
    from node.mac.band_airtime import WaitTime
    from models.model import SpreadingFactor, CodingRate
    from node.protocol.parameters import ParametersDict, ParametersType



BROADCAST_ADDRESS = NodeID(255)
NETWORK_ID = b"\x0E\x1F\x7D\x2C"

class CommandsMixin:
    rfm9x: "RFM9x"
    node_id: int
    rtc: "RTC"

    spreading_factor: "SpreadingFactor"
    bandwidth: int
    coding_rate: "CodingRate"
    wait_horizon_sec: "WaitTime"

    if TYPE_CHECKING:
        # pylint: disable=unused-argument
        def apply_link_profile(
            self,
            sf: SpreadingFactor,
            bw: int,
            cr: CodingRate,
            tx_power_dbm: int,
            crc: bool = True,
            preamble: int = 8,
        ) -> None: ...

        def control_receive(
            self,
            expected_parameter: ParametersType,
            listen_window: Optional[float] = None,
        ) -> Optional[ParametersDict]: ...


    def network_join(
        self,
        listen_window: "Optional[float]",
        now: "Optional[float]" = None,
    ) -> None:
        now = monotonic() if now is None else now
        r = self.rfm9x

        message = add_parameter(None, CommandParameters.NETWORK_JOIN, NETWORK_ID.decode()) #  pylint: disable=assignment-from-no-return
        current_time = self.rtc.datetime
        message = add_timestamp(current_time, message) # pylint: disable=assignment-from-no-return

        packet = Packet(self.node_id, BROADCAST_ADDRESS, PacketKind.CONTROL, 0, message)

        deadline = monotonic() + (listen_window if listen_window else float(self.wait_horizon_sec))

        while monotonic() < deadline:
            r.send(
                packet.to_byte(),
                destination=packet.target,
                node=packet.source,
                identifier=packet.identifier,
                flags=packet.p_type
            )
        sleep(0.25)

        self.control_receive( # pylint: disable=assignment-from-no-return
            CommandParameters.NETWORK_JOIN,
            listen_window=self.wait_horizon_sec,
        )
