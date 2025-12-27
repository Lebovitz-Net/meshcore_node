# Pseudocode for wiring

mesh_node = MeshCoreNode(
    identity=local_identity,
    send_raw=radio.send,          # or a wrapper around MeshcoreServer's TX
    emit_event=client_api.emit,   # your existing event bus
)

def on_radio_packet(raw_bytes: bytes, snr: float, rssi: float):
    mesh_node.on_raw_packet(raw_bytes, snr=snr, rssi=rssi)

radio.on("packet", on_radio_packet)   # or whatever your EventEmitter API is
