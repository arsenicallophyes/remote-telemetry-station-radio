from node.transport.peer import Peer, HALF, MAX_SEQ
from node.transport.types.sequence_response import SequenceResponse, SequenceResponseType
from models.model import NodeID
from node.transport.types.recovery_state import RecoveryState

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Dict, Optional

class PeerTable:

    def __init__(self) -> None:
        self.peers: "Dict[NodeID, Peer]" = {}

    def add_peer(self, node_id: NodeID) -> bool:
        peer = self.peers.get(node_id)

        if peer is None:
            self.peers[node_id] = Peer(node_id)
            return True

        return False

    def remove_peer(self, node_id: NodeID) -> bool:
        if self.get_peer(node_id):
            self.peers.pop(node_id)
            return True

        return False

    def get_peer(self, node_id: NodeID) -> "Optional[Peer]":
        return self.peers.get(node_id)


    def handle_sequence(self, node_id: NodeID, seq: int) -> SequenceResponseType:
        """
        returns SequenceResponse
        """
        peer = self.get_peer(node_id)
        if peer is None:
            print("Unregistered Peer")
            return SequenceResponse.UNREGISTERED

        expected = peer.receive.expected_seq
        delta = peer.receive.seq_delta(seq, expected)

        if delta == 0:
            print("success", seq)
            peer.receive.increment_sequence()
            return SequenceResponse.SUCCESS

        if 0 < delta < HALF:
            print("logging and sending nack", seq)
            peer.receive.missed_packets = tuple((expected + i) % MAX_SEQ for i in range(delta))

            return SequenceResponse.AHEAD

        print("discarding", seq)
        return SequenceResponse.DUPLICATE

    def handle_sequence_recovery(
            self,
            node_id: NodeID,
            identifier: int,
            recovery: RecoveryState,
        ) -> SequenceResponseType:

        peer = self.get_peer(node_id)
        if peer is None:
            print("Unregistered Peer")
            return SequenceResponse.UNREGISTERED

        if identifier in recovery.queued_packets:
            recovery.queued_packets.discard(identifier)
            return SequenceResponse.SUCCESS

        return SequenceResponse.ABORT
