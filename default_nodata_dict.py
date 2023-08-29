import numpy as np

nodata_values = {
    'int8': -128,
    'int16': -32768,
    'int32': -2147483648,
    'int64': -9223372036854775808,
    'uint8': 0,
    'uint16': 65535,
    'uint32': 4294967295,
    'uint64': 2**64 - 1,
    'float16': -9999.0,
    'float32': -9999.0,
    'float64': -9999.0,
}