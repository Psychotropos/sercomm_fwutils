# sercomm_fwutils
Tools to manipulate the firmware images of certain Sercomm-made consumer networking devices

Only tested with Python 2.7, some edits may be required in order for the utilities to work with Python 3+.
Requires the pycrypto package (https://pypi.python.org/pypi/pycrypto)

# Usage
- use `python frontier.py <firmware>.img` to decrypt the images
- use `python psychiatrist.py <firmware>_dump.bin` to extract the firmware parts
- (modify or do whatever you want with the created `blocks/kernel_rootfs_<version>.bin`)
- use `python etoh.py` to repack the firmware image
