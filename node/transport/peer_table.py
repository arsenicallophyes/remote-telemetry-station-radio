from node.transport.peer import Peer, HALF, MAX_SEQ
from node.transport.types.sequence_response import SequenceResponse, SequenceResponseType
from node.transport.types.recovery_state import RecoveryState
from node.transport.types.authorization_state import AuthorizationStateType, AuthorizationState

from models.model import NodeID, Identifier


try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Dict, Optional

class PeerTable:

    def __init__(self) -> None:
        self.peers: "Dict[NodeID, Peer]" = {}

    def add_peer(
        self,
        node_id: NodeID,
        state: AuthorizationStateType,
        sequence: "Optional[Identifier]" = None,
    ) -> bool:
        peer = self.peers.get(node_id)

        if peer is None:
            peer = Peer(node_id, state)
            if sequence is not None:
                peer.receive.set_sequence(sequence)
            self.peers[node_id] = peer

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
        if not peer:
            print("Unregistered Peer")
            return SequenceResponse.UNREGISTERED

        if peer.state == AuthorizationState.PENDING:
            return SequenceResponse.PENDING

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
        if not peer:
            print("Unregistered Peer")
            return SequenceResponse.UNREGISTERED

        if peer.state == AuthorizationState.PENDING:
            return SequenceResponse.PENDING

        if identifier in recovery.queued_packets:
            recovery.queued_packets.discard(identifier)
            return SequenceResponse.SUCCESS

        return SequenceResponse.ABORT
