# EtOH: Firmware builder for Sercomm devices, tested with images from T-Mobile's Speedport W 724V Type Ci (OTE & T-Mobile variants)
# DISCLAIMER: I take no responsibility for any damage that may be caused to your device if you flash an EtOH-produced image to it. The resulting images have been compared and found to match with most OTEnet-ACSRepo issued images.
# In some instances, there was some extra padding at the end of the original image, but since the image is fruncate()'d down to the length specified in the header, it should not matter.
# It is your responsibility to verify the integrity of any images produced by EtOH.
import cStringIO
import glob
import os
import sys
import gzip_mod
from sercomm_common import *
from Crypto.Cipher import AES

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
