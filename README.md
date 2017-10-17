# sercomm_fwutils
Tools to manipulate the firmware images of certain Sercomm-made consumer networking devices.
Known to support the Speedport W724 Type C/Ci variants, as well as some devices from the Sercomm SGH series.

Only tested with Python 2.7, some edits may be required in order for the utilities to work with Python 3+.

Requires the pycrypto package (https://pypi.python.org/pypi/pycrypto)

# Usage
- use `python decrypt_image.py <firmware>.img <output>.img` to decrypt the images
- use `python decompress_image.py <decrypt_output>.bin <target_directory>` to extract the firmware parts
- (modify or do whatever you want with the created `<target_directory>/kernel_rootfs_<version>.bin`)
- use `python create_image.py <input_directory> <firmware_output> <firmware_type>` to repack the firmware image

