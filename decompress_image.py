from image_types import *
import sys
import os

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('[-] Usage: python decrypt_image.py <in_file> <out_folder>')
        sys.exit(1)

    in_file, out_folder = sys.argv[1:]
    file_data = open(in_file, 'rb').read()
    image = Stage2(file_data)
    if not image.validateType():
        print('[-] Image validation failed! Make sure you are passing the output file of decrypt_image.')
        sys.exit(2)

    try:
        os.mkdir(out_folder)
    except:
        pass

    os.chdir(out_folder)
    image.extractHeader()
    image.extractBlocks()
    image.writeManifest()
    print('[+] Done!')
