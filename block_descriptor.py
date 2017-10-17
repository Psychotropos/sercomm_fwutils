class BlockDescriptor:
    def __init__(self, block_name, block_version, block_filename):
        self.block_name = block_name
        self.block_version = block_version
        self.block_filename = block_filename

    def asDict(self):
        return dict(block_name=self.block_name, block_version=self.block_version, block_filename=self.block_filename)

    def __repr__(self):
        return 'BlockDescriptor <block name: %s, block version: %s, block filename: %s' % (self.block_name, self.block_version, self.block_filename)
