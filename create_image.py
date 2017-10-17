from image_types import *
import sys
import os

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('[-] Usage: python create_image.py <in_dir> <out_file> <image_type>')
        sys.exit(1)

    in_dir, out_file, image_type = sys.argv[1:]
    image_type = int(image_type)
    if image_type not in [1, 2]:
        print('[-] Specify firmware image type (1 or 2).')
        sys.exit(2)

    os.chdir(in_dir)
    stage2_image = Stage2('', read=False)
    stage2_image.readManifest()
    fw_ver = None
    for block in stage2_image.blocks:
        if block.block_name == 'kernel_rootfs':
            fw_ver = block.block_version
            break

    if fw_ver is None:
        print('[-] Failed to find kernel_rootfs block, cannot proceed!')
        sys.exit(3)

    stage2_data = stage2_image.createImage()
    print('[+] Built stage2 image, building container...')
    if image_type == 1:
        image = Type1('', read=False)
    else:
        image = Type2('', read=False)

    image_data = image.createImage(fw_ver, stage2_data)
    open(out_file, 'wb').write(image_data)
    print('[+] Wrote output image to %s successfully!' % out_file)
