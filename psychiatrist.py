# Psychiatrist - Firmware extractor for Sercomm devices, tested with images from T-Mobile's Speedport W 724V Type Ci (OTE & T-Mobile variants)
import sys
import os
import gzip
import cStringIO
import hashlib

def strip_nulls(str):
	return str.strip('\x00')

def calculate_digest(stream):
	# Sending those signals, those digital signals.
	ctx = hashlib.sha256()
	while True:
		chunk = stream.read(16384)
		if not chunk:
			break
		ctx.update(chunk)
	return ctx.digest()

def dump_blocks(stream):
	while True:
		block_name = strip_nulls(stream.read(32))
		if not block_name: 
			break
		payloadSize = int(strip_nulls(stream.read(32)))
		block_version = strip_nulls(stream.read(32))
		stream.read(32) # Padding
		payload = stream.read(payloadSize)
		filename = block_name + '_' + block_version + '.bin'
		try:
			f = open('blocks//' + filename, 'wb')
			f.write(payload)
			f.close()
			print '[+] Wrote ' + filename + ' to disk'
		except IOError:
			print '[-] Failed to write firmware block ' + filename + ' to drive. Exiting.'
			sys.exit()

def verify_digest(stream, expectedDigest):
	digest = calculate_digest(stream)
	stream.seek(0)
	return digest == expectedDigest

def dump_dev_hdr(hdr):
	try:
		f = open('blocks//dev_hdr.bin', 'wb')
		f.write(hdr)
		f.close()
		print '[+] Wrote device header to dev_hdr.bin'
	except IOError:
		print '[-] Failed to acquire file handle to write device header!'

if len(sys.argv) == 2:
	try:
		try:
			os.mkdir('blocks') 
		except:
			pass # Directory already exists, that's fine.
		f = open(sys.argv[1], 'rb')
		dev_hdr = f.read(128)
		digest = f.read(32)
		mappedFile = cStringIO.StringIO()
		mappedFile.write(f.read())
		mappedFile.seek(0)
		print '[+] Archive digest is: ' + digest.encode('hex')
		if not verify_digest(mappedFile, digest):
			print '[-] Failed to verify image. Exiting.'
			sys.exit()
		gzStream = gzip.GzipFile(fileobj=mappedFile, mode='rb')
		dump_blocks(gzStream)
		dump_dev_hdr(dev_hdr)
	except IOError:
		print '[-] Failed to acquire file handle to image!'
else:
	print '[-] Usage: python psychiatrist.py dumped_img'
