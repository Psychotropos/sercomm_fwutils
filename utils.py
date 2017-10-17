def nullpad_str(s, length):
    return s + ('\x00' * (length - len(s)))

def unnullpad_str(s):
    if '\x00' not in s:
        return s

    return s.split('\x00')[0]

def pkcs7_pad(s):
    pad_length = 16 - (len(s) % 16)
    return s + (chr(pad_length) * pad_length)
