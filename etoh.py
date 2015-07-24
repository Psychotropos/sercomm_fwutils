# EtOH: Firmware builder for Sercomm devices, tested with images from T-Mobile's Speedport W 724V Type Ci (OTE & T-Mobile variants)
import cStringIO
import hashlib
import glob
import os
import sys
import gzip_mod
from Crypto.Cipher import AES

def nullpad_str(str, length):
	return str + ('\x00' * (length - len(str)))

def calculate_digest(data):
	# Sending those signals, those digital signals.
	stream = cStringIO.StringIO(data)
	ctx = hashlib.sha256()
	while True:
		chunk = stream.read(16384)
		if not chunk:
			break
		ctx.update(chunk)
	return ctx.digest()

def calc_key_from_info(rootfs_ver, image_size):
	ctx1 = hashlib.md5()
	ctx1.update('\x00' * 32) # Padding
	ctx1.update(nullpad_str(rootfs_ver, 32))
	ctx2 = hashlib.md5()
	ctx2.update(nullpad_str(str(image_size), 32))
	ctx2.update(nullpad_str(rootfs_ver, 32))
	return ctx1.digest() + ctx2.digest()

def create_hdr_from_info(rootfs_ver, image_size):
	# iv = '\x19\xB6\x5C\x97\xF8\xD1\x4B\x3A\x0F\xA0\x1A\xCB\x6D\xEA\xB7\x59\xD6\x8B\x9E\x42\xFC\xE4\x43\x39\xDB\x88\xE5\x25\x43\xA0\x25\xE5' # 53A image
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

def get_tuple_from_block_path(path):
	if len(path) > 1:
		print '[-] Detected more than one of the same block type in the block directory: ' + str(path) + '. Exiting.'
		sys.exit()
	path = path[0]
	if sys.platform == 'win32':
		name = path.split('\\')[1][:-4]
	else:
		name = path.split('/')[1][:-4]
	blck_info = name.rsplit('_', 1) # First part is the block type, second one's the version.
	return (path, blck_info[0], blck_info[1])

def get_blocks():
	rootfs = glob.glob('blocks//kernel_rootfs*.bin')
	bootloader = glob.glob('blocks//bootloader*.bin')
	dect = glob.glob('blocks//dect_rom*.bin')
	if dect:
		return (get_tuple_from_block_path(rootfs), get_tuple_from_block_path(bootloader), get_tuple_from_block_path(dect))
	else:
		return (get_tuple_from_block_path(rootfs), get_tuple_from_block_path(bootloader))

def pkcs7_pad(str):
	pad_length = 16 - (len(str) % 16)
	return str + (chr(pad_length) * pad_length)

def create_image():
	try:
		f = open('blocks//dev_hdr.bin', 'rb')
		dev_hdr = f.read()
		f.close()
	except IOError:
		print '[-] Failed to read device header. Exiting.'
		sys.exit()
	get_blocks()
	stream = cStringIO.StringIO()
	blocks = get_blocks()
	for block in blocks:
		print '[+] Writing ' + block[1] + ' version ' + block[2]
		f = open(block[0], 'rb')
		stream.write(nullpad_str(block[1], 32))
		stream.write(nullpad_str(str(os.path.getsize(block[0])), 32))
		stream.write(nullpad_str(block[2], 32))
		stream.write('\x00' * 32) # Padding
		stream.write(f.read())
	stream.seek(0)
	gzipStream = cStringIO.StringIO()
	gzip = gzip_mod.GzipFile(filename = None, mode = 'wb', fileobj = gzipStream, compresslevel = 6)
	gzip.write(stream.read())
	gzip.close()
	gzipStream.seek(0)
	print '[+] Finished image compression'
	payload = gzipStream.read()
	imgStream = cStringIO.StringIO()
	imgStream.write(dev_hdr)
	imgStream.write(nullpad_str(calculate_digest(payload), 32))
	imgStream.write(payload)
	imgStream.seek(0)
	print '[+] Finished crafting stage_2 image'
	payload = imgStream.read()
	hdr = create_hdr_from_info(blocks[0][2], len(payload))
	aes = AES.new(hdr[1], AES.MODE_CBC, hdr[2][:16])
	payload = aes.encrypt(pkcs7_pad(payload))
	finalStream = cStringIO.StringIO()
	finalStream.write(hdr[0])
	finalStream.write(payload)
	finalStream.seek(0)
	filename = blocks[0][2] + '_EtOH.img'
	print '[+] Finished crafting image, writing to ' + filename
	f = open(filename, 'wb')
	f.write(finalStream.read())
	f.close()

create_image()
