from utils import *
from block_descriptor import *
from Crypto.Cipher import AES
import hashlib
from io import BytesIO
import gzip
import json
import gzip_mod
import os


class Image:
    def __init__(self, image_data, read=True):
        self.stream = BytesIO(image_data)
        self.stream_len = len(image_data)
        if read:
            self.readHeader()

    def getBody(self):
        cur_pos = self.stream.tell()
        self.stream.seek(0xA0)
        body = self.stream.read()
        self.stream.seek(cur_pos)
        return body

    def readHeader(self):
        # Header size appears to universally be 0xA0 (160) bytes, with 32 bytes alloted per field.
        raise Exception('readHeader not implemented for class %s!' % self.__class__.__name__)

    def validateType(self):
        raise Exception('No validateType implemented for class %s!' % self.__class__.__name__)

    def getKeyPair(self):
        raise Exception('No getKeyPair implemented for class %s' % self.__class__.__name__)

    def decryptImage(self):
        # Firmware images for Sercomm devices appear to universally use AES 256 in CBC mode.
        if not hasattr(self, 'filesize'):
            raise Exception('decryptImage called before readHeader!')

        key_pair = self.getKeyPair()
        aes = AES.new(key=key_pair['key'], mode=AES.MODE_CBC, IV=key_pair['iv'])
        cur_pos = self.stream.tell()
        # Seek past the header (remember, always 160 bytes!)
        self.stream.seek(0xA0)
        plaintext_body = aes.decrypt(self.stream.read())
        return plaintext_body[:self.filesize]


class Stage2(Image):
    def readHeader(self):
        self.device_header = self.stream.read(128)
        self.image_digest = self.stream.read(32)
        self.blocks = []

    def validateType(self):
        if not hasattr(self, 'device_header'):
            raise Exception('validateType called before readHeader!')

        digest = hashlib.new('sha256')
        digest.update(self.getBody())
        return digest.digest() == self.image_digest

    def extractHeader(self):
        if not hasattr(self, 'device_header'):
            raise Exception('extractHeader called before readHeader!')

        try:
            open('dev_hdr.bin', 'wb').write(self.device_header)
        except IOError:
            print('[-] Failed to write device header to file!')

    def extractBlocks(self):
        cur_pos = self.stream.tell()
        self.stream.seek(0xA0)
        gzip_stream = gzip.GzipFile(fileobj=self.stream, mode='rb')
        while True:
            block_name = unnullpad_str(gzip_stream.read(32))
            if not block_name:
                break

            payload_size = int(unnullpad_str(gzip_stream.read(32)))
            block_version = unnullpad_str(gzip_stream.read(32))
            gzip_stream.read(32) # Padding?

            try:
                file_name = '%s_%s.bin' % (block_name, block_version)
                open(file_name, 'wb').write(gzip_stream.read(payload_size))
                self.blocks.append(BlockDescriptor(block_name, block_version, file_name))
                print('[+] Wrote block %s version %s to file!' % (block_name, block_version))
            except IOError:
                print('[-] Failed to write block %s to file!' % block_name)

        self.stream.seek(cur_pos)

    def readManifest(self):
        self.blocks = []
        manifest_data = json.loads(open('manifest.json', 'rb').read())
        if 'blocks' not in manifest_data:
            raise Exception('Invalid firmware manifest provided!')

        for block in manifest_data['blocks']:
            self.blocks.append(BlockDescriptor(block['block_name'], block['block_version'], block['block_filename']))


    def writeManifest(self):
        block_manifests = []
        for block in self.blocks:
            block_manifests.append(block.asDict())

        manifest_data = dict(blocks=block_manifests)
        try:
            open('manifest.json', 'wb').write(json.dumps(manifest_data))
        except IOError:
            print('[-] Failed to write manifest to file!')

    def createImage(self):
        self.stream = BytesIO()
        content_stream = BytesIO()
        gzip_wrapper = gzip_mod.GzipFile(filename = None, mode = 'wb', fileobj = content_stream, compresslevel = 6)
        for block in self.blocks:
            print('[+] Writing block with name %s and version %s to stream...' % (block.block_name, block.block_version))
            gzip_wrapper.write(nullpad_str(block.block_name, 32))
            gzip_wrapper.write(nullpad_str(str(os.path.getsize(block.block_filename)), 32))
            gzip_wrapper.write(nullpad_str(block.block_version, 32))
            gzip_wrapper.write('\x00' * 32) # Padding
            gzip_wrapper.write(open(block.block_filename, 'rb').read())
        gzip_wrapper.close()
        content_stream.seek(0)
        body_digest = hashlib.new('sha256')
        body_digest.update(content_stream.read())
        content_stream.seek(0)
        self.stream.write(open('dev_hdr.bin', 'rb').read())
        self.stream.write(body_digest.digest())
        self.stream.write(content_stream.read())
        self.stream.seek(0)
        self.readHeader()
        assert self.validateType() # Make sure we can pass our own validation checks
        self.stream.seek(0)
        return self.stream.read()


class Type1(Image):
    def readHeader(self):
        self.nullpad = self.stream.read(32)
        self.fw_version = unnullpad_str(self.stream.read(32))
        self.iv = self.stream.read(32)
        self.nullpad2 = self.stream.read(32)
        self.filesize = int(unnullpad_str(self.stream.read(32)))
        assert self.stream.tell() == 0xA0

    def validateType(self):
        return self.nullpad == ('\x00' * 32) and self.nullpad2 == ('\x00' * 32)

    def getKeyPair(self):
        if not hasattr(self, 'fw_version'):
            raise Exception('validateType called before readHeader!')

        digest_1 = hashlib.new('md5')
        digest_1.update(self.nullpad2)
        digest_1.update(nullpad_str(self.fw_version, 32))
        digest_2 = hashlib.new('md5')
        digest_2.update(nullpad_str(str(self.filesize), 32))
        digest_2.update(nullpad_str(self.fw_version, 32))
        key = digest_1.digest() + digest_2.digest()
        return dict(key=key, iv=self.iv[:16])

    def createImage(self, fw_version, stage2_image):
        self.stream = BytesIO()
        self.nullpad = '\x00' * 32
        self.nullpad2 = '\x00' * 32
        self.fw_version = fw_version
        self.filesize = len(stage2_image)
        self.iv = os.urandom(32)
        image_key = self.getKeyPair()
        aes = AES.new(key=image_key['key'], mode=AES.MODE_CBC, IV=image_key['iv'][:16]) # NB: Only the first 16 bytes are used
        self.stream.write(self.nullpad) # Padding
        self.stream.write(nullpad_str(self.fw_version, 32))
        self.stream.write(self.iv)
        self.stream.write(self.nullpad2) # More padding
        self.stream.write(nullpad_str(str(self.filesize), 32))
        self.stream.write(aes.encrypt(pkcs7_pad(stage2_image)))
        self.stream.seek(0)
        self.readHeader()
        assert self.validateType()
        self.stream.seek(0)
        return self.stream.read()

class Type2(Image):
    def readHeader(self):
        self.image_digest = self.stream.read(32)
        self.fw_version = unnullpad_str(self.stream.read(32))
        self.key_factor = self.stream.read(32)
        self.iv = self.stream.read(32)
        self.filesize = int(unnullpad_str(self.stream.read(32)))
        assert self.stream.tell() == 0xA0

    def validateType(self):
        if not hasattr(self, 'fw_version'):
            raise Exception('validateType called before readHeader!')

        cur_pos = self.stream.tell()
        self.stream.seek(32) # Skip original image digest
        digest = hashlib.new('sha256')
        digest.update((b'\x00' * 32) + self.stream.read())
        self.stream.seek(cur_pos)
        return digest.digest() == self.image_digest

    @staticmethod
    def keyPermutator(key):
        perm_tbl = '26aejsw37bfktx48chmuy59dipvz'
        key = bytearray(key)
        for i in xrange(len(key)):
            key[i] = perm_tbl[key[i] % len(perm_tbl)]
        return str(key)

    def getKeyPair(self):
        digest_1 = hashlib.new('md5')
        digest_1.update(self.key_factor)
        digest_1.update(self.fw_version)
        digest_2 = hashlib.new('md5')
        digest_2.update('b7293e8150d1330c6c3d93f2fa81331b')
        digest_2.update(self.fw_version)
        digest_3 = hashlib.new('md5')
        digest_3.update('83f323b7132703029da5f4a9daa72a60')
        digest_3.update(self.fw_version)
        digest_fin = hashlib.new('md5')
        digest_fin.update(digest_1.digest())
        digest_fin.update(digest_2.digest())
        digest_fin.update(digest_3.digest())
        key = Type2.keyPermutator(sercomm_hexdigest(digest_fin.digest()))
        return dict(key=key, iv=self.iv[:16])

    def createImage(self, fw_version, stage2_image):
        self.stream = BytesIO()
        self.fw_version = fw_version
        self.filesize = len(stage2_image)
        self.key_factor = os.urandom(32)
        #self.iv = os.urandom(32)
        self.iv = '\x00' * 32
        image_key = self.getKeyPair()
        aes = AES.new(key=image_key['key'], mode=AES.MODE_CBC, IV=image_key['iv'][:16]) # NB: Only the first 16 bytes are used
        self.stream.write('\x00' * 32) # Null digest for initial digest calculation
        self.stream.write(nullpad_str(self.fw_version, 32))
        self.stream.write(self.key_factor)
        self.stream.write(self.iv)
        self.stream.write(nullpad_str(str(self.filesize), 32))
        self.stream.write(aes.encrypt(pkcs7_pad(stage2_image)))
        self.stream.seek(0)
        digest = hashlib.new('sha256')
        digest.update(self.stream.read()) # Now overwrite it with the actual image digest
        self.stream.seek(0)
        self.stream.write(digest.digest())
        self.stream.seek(0)
        self.readHeader()
        assert self.validateType()
        self.stream.seek(0)
        return self.stream.read()
