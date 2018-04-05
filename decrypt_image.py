from image_types import *
import sys

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('[-] Usage: python decrypt_image.py <in_file> <out_file>')
        sys.exit(1)

    in_file, out_file = sys.argv[1:]
    file_data = open(in_file, 'rb').read()
    print('[+] Trying to interpret file as type1 image...')
    image = Type1(file_data)
    if not image.validateType():
        print('[-] File does not appear to be a valid type1 image, trying type2...')
        image = Type2(file_data)
        if not image.validateType():
            print('[-] Not a type2 image either, exiting')
            sys.exit(2)
    aes_info = image.getKeyPair()
    print('[+] Image key: %s' % aes_info['key'].encode('hex'))
    print('[+] Image IV: %s' % aes_info['iv'].encode('hex'))
    open(out_file, 'wb').write(image.decryptImage())
    print('[+] Wrote decrypted image to %s!' % out_file)
