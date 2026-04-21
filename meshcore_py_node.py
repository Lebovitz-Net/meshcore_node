#!/usr/bin/env python3
import time
from sx1262_driver import SX1262, RX_CONTINUOUS, TX_SINGLE
from meshcore_py_node import MeshCoreNode, LocalStore

# ------------------------------------------------------------
# Radio pin mapping
# ------------------------------------------------------------
BUSY_PIN = 20
RESET_PIN = 18
NSS_PIN = 21
SPI_BUS = 0
SPI_DEV = 0

# ------------------------------------------------------------
# MeshCore integration callbacks
# ------------------------------------------------------------

def make_send_raw(radio):
    def send_raw(data: bytes):
        radio.begin_packet()
        radio.put(data)
        ok = radio.end_packet(TX_SINGLE)
        if not ok:
            print("TX failed")
    return send_raw

def emit_event(event, data):
    print(f"[EVENT] {event}: {data}")

# ------------------------------------------------------------
# RX handler → feed into MeshCoreNode
# ------------------------------------------------------------

async def handle_rx_done(payload_length=None, buffer_index=None, irq_status=None):
    raw = radio.get(payload_length)
    rssi = radio.packet_rssi()
    snr = radio.snr()

    node.on_raw_packet(raw, snr=snr, rssi=rssi)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    global radio, node

    print("Initializing SX1262…")
    radio = SX1262()

    ok = radio.begin(
        bus=SPI_BUS,
        cs=SPI_DEV,
        reset=RESET_PIN,
        busy=BUSY_PIN,
        irq=-1,
        txen=-1,
        rxen=-1,
        wake=-1,
    )
    if not ok:
        raise RuntimeError("SX1262 failed to initialize")

    # Configure radio
    # MeshCore sync word (0x1242) — NOT the LoRaWAN public sync word (0x3444)
    radio.set_sync_word(0x1242)
    radio.set_frequency(910_525_000)
    radio.set_lora_modulation(sf=7, bw=62_500, cr=5, ldro=False)
    radio.set_lora_packet(
        header_type=0,  # HEADER_EXPLICIT
        preamble_length=12,
        payload_length=255,  # MeshCore packets vary in size
        crc_type=True,
        invert_iq=False,
    )

    # Create MeshCore node
    store = LocalStore()
    node = MeshCoreNode(
        identity=store.identity,
        send_raw=make_send_raw(radio),
        emit_event=emit_event,
        store=store,
    )

    # Register RX handler
    radio.on("rx_done", handle_rx_done)

    print("Entering RX_CONTINUOUS…")
    radio.request(RX_CONTINUOUS)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        radio.end()

if __name__ == "__main__":
    main()
