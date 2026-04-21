# meshcore_py_node/constants.py

# 1-byte hash prefix for V1 packets (MeshCore < 1.114.0)
PATH_HASH_SIZE_V1 = 1

# 2-byte hash prefix for V2 packets (MeshCore 1.114.0+ 2-byte tracing)
PATH_HASH_SIZE_V2 = 2

# Default (backward-compatible alias)
PATH_HASH_SIZE = PATH_HASH_SIZE_V1

# MAC length for AES-128-GCM-style tags (16 bytes)
MAC_LEN = 16

# Maximum path buffer size in bytes (matches MAX_PATH_SIZE in firmware)
MAX_PATH_LEN = 64
