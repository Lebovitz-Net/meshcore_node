from meshcore_node import MeshCoreNode, LocalStore

def send_raw(data: bytes):
    # Replace with SX1262, serial, UDP, etc.
    print("TX:", data.hex())

def emit_event(event: str, data: dict):
    print("EVENT:", event, data)

store = LocalStore()
node = MeshCoreNode(
    identity=store.identity,
    send_raw=send_raw,
    emit_event=emit_event,
    store=store,
)

# Send an ADVERT
node.send_advert(b"hello")
