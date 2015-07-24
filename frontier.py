# Frontier - Firmware decrypter for Sercomm devices, tested with images from T-Mobile's Speedport W 724V Type Ci (OTE & T-Mobile variants)
# ctx3 = md5.new()
# ctx3.update('\x53\x70\x65\x65\x64\x70\x6F\x72\x74\x20\x57\x20\x37\x32\x34\x56\x00\x00\x00\x00\x25\x73\x3A\x20\x73\x6B\x69\x70\x20\x6F\x66\x74')
# ctx3.update(hdr[1])
# ctx4 = md5.new()
# ctx4.update(ctx1.digest() + ctx2.digest() + ctx3.digest())
# These are calculated but never actually used, so we take them out.
import sys
import md5
from Crypto.Cipher import AES

def strip_nulls(str):
	return str.strip('\x00')

def read_img(filename):
	f = open(filename, 'rb')
	nullpad = f.read(32)
	ver = f.read(32)
	iv = f.read(32) # Only the first 16 bytes are used as the IV.
	nullpad2 = f.read(32)
	filesize = f.read(32)
	remaining = f.read()
	return (nullpad, ver, iv, nullpad2, filesize, remaining)

def calc_key_and_iv_from_img(image):
	ctx1 = md5.new()
	ctx1.update(image[3])
	ctx1.update(image[1])
	ctx2 = md5.new()
	ctx2.update(image[4])
	ctx2.update(image[1])
	return (ctx1.digest() + ctx2.digest(), image[2][:16])

def dump_image(image, key_iv):
	aes = AES.new(key_iv[0], AES.MODE_CBC, key_iv[1])
	return aes.decrypt(image[5])[:int(strip_nulls(image[4]))] # Decrypt and truncate output to expected size specified in the header (the rest of it is PKCS#7 padding)

if len(sys.argv) == 2:
	img = read_img(sys.argv[1])
	key_iv = calc_key_and_iv_from_img(img)
	print '[+] Key is: ' + key_iv[0].encode('hex')
	print '[+] IV is: ' + key_iv[1].encode('hex')
	filename = sys.argv[1][:-4] + '_dump.bin'
	try:
		f = open(filename, 'wb')
		f.write(dump_image(img, key_iv))
		f.close()
		print '[+] Image dumped to ' + filename
	except IOError:
		print '[-] Failed to acquire handle to output file!'
else:
	print '[-] Syntax: python frontier.py img'
