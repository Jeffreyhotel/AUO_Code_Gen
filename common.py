import os

def b2hstr(b: bytes) -> str:
    s = ""
    for i in range(len(b)):
        s += ("{0:02x} ").format(b[i])
    return s[:-1].upper()
