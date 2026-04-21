from meshcore_py_node.node import MeshCoreNode
from meshcore_py_node.packet.header import PayloadVersion


class MeshCoreRouter(MeshCoreNode):
    def __init__(self, identity, send_raw, emit_event, store,
                 version: PayloadVersion = PayloadVersion.V1):
        # Routers have an identity for path-appending but do not decrypt user messages
        if identity is None:
            raise ValueError("MeshCoreRouter requires an identity (used for path/trace hash appending)")
        super().__init__(
            identity=identity,
            send_raw=send_raw,
            emit_event=emit_event,
            store=store,
            is_router=True,
            version=version,
        )

    # Disable all user-initiated sends
    def send_advert(self, *args, **kwargs):
        raise RuntimeError("Router nodes cannot send adverts")

    def send_direct(self, *args, **kwargs):
        raise RuntimeError("Router nodes cannot send direct messages")

    def send_group(self, *args, **kwargs):
        raise RuntimeError("Router nodes cannot send group messages")

    def send_path(self, *args, **kwargs):
        raise RuntimeError("Router nodes cannot originate PATH packets")

    def send_trace(self, *args, **kwargs):
        raise RuntimeError("Router nodes cannot originate TRACE packets")

    def send_raw_custom(self, *args, **kwargs):
        raise RuntimeError("Router nodes cannot originate RAW_CUSTOM packets")

    # Optional: override local handling to suppress events
    def _handle_packet(self, pkt):
        # Routers do not decrypt or emit events
        return
