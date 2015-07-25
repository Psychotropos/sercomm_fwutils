import hashlib
import cStringIO

def strip_nulls(str):
	return str.strip('\x00')

def calculate_digest(data):
	stream = cStringIO.StringIO(data)
	ctx = hashlib.sha256()
	while True:
		chunk = stream.read(16384)
		if not chunk:
			break
		ctx.update(chunk)
	return ctx.digest()

def verify_digest(stream, expectedDigest):
	digest = calculate_digest(stream.read())
	stream.seek(0)
	return digest == expectedDigest

def nullpad_str(str, length):
	return str + ('\x00' * (length - len(str)))

def pkcs7_pad(str):
	pad_length = 16 - (len(str) % 16)
	return str + (chr(pad_length) * pad_length)

def calc_key_from_info(rootfs_ver, image_size):
	ctx1 = hashlib.md5()
	ctx1.update('\x00' * 32) # Padding
	ctx1.update(nullpad_str(rootfs_ver, 32))
	ctx2 = hashlib.md5()
	ctx2.update(nullpad_str(str(image_size), 32))
	ctx2.update(nullpad_str(rootfs_ver, 32))
	return ctx1.digest() + ctx2.digest()

def create_hdr_from_info(rootfs_ver, image_size):
	#iv = '\x19\xB6\x5C\x97\xF8\xD1\x4B\x3A\x0F\xA0\x1A\xCB\x6D\xEA\xB7\x59\xD6\x8B\x9E\x42\xFC\xE4\x43\x39\xDB\x88\xE5\x25\x43\xA0\x25\xE5' # 53A image
	key = calc_key_from_info(rootfs_ver, image_size)
	iv = os.urandom(32) # 32 random bytes, only the first 16 are used
	hdr = cStringIO.StringIO()
	hdr.write('\x00' * 32) # Padding
	hdr.write(nullpad_str(rootfs_ver, 32))
	hdr.write(iv)
	hdr.write('\x00' * 32) # More padding
	hdr.write(nullpad_str(str(image_size), 32))
	hdr.seek(0)
	return (hdr.read(), key, iv)

def calc_key_and_iv_from_img(image):
	return (calc_key_from_info(strip_nulls(image[1]), int(strip_nulls(image[4]))), image[2][:16])
