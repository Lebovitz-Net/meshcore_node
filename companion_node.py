from meshcore_py_node.node import MeshCoreNode
from meshcore_py_node.packet.header import PayloadVersion


class MeshCoreCompanion(MeshCoreNode):
    def __init__(self, identity, send_raw, emit_event, store,
                 version: PayloadVersion = PayloadVersion.V1):
        super().__init__(
            identity=identity,
            send_raw=send_raw,
            emit_event=emit_event,
            store=store,
            is_router=False,
            version=version,
        )
