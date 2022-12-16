def nullpad_str(s, length):
    return s + ('\x00' * (length - len(s)))

def unnullpad_str(s):
    s = s.decode()
    if '\x00' not in s:
        return s

    return s.split('\x00')[0]

def pkcs7_pad(s):
    pad_length = 16 - (len(s) % 16)
    return s + (chr(pad_length) * pad_length)

def sercomm_hexdigest(s):
    # Replicates a really odd behaviour in the Sercomm libfwutil implementation of hex-digest to hex-string
    # Hexadecimal digits starting prefixed with a '0' have their leading zero removed and are followed by a trailing null byte.
    hex_s = ''
    for c in s:
        c_hex = c.encode('hex')
        if c_hex.startswith('0'):
            hex_s += c_hex[1:]
            hex_s += '\x00'
        else:
            hex_s += c_hex
    return hex_s
