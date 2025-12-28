class MeshCoreCompanion(MeshCoreNode):
    def __init__(self, identity, send_raw, emit_event, store):
        super().__init__(
            identity=identity,
            send_raw=send_raw,
            emit_event=emit_event,
            store=store,
            is_router=False,
        )
