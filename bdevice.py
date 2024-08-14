# bdevice.py Hardware-agnostic base classes.
# BlockDevice Base class for general block devices e.g. EEPROM, FRAM.
# FlashDevice Base class for generic Flash memory (subclass of BlockDevice).
# Documentation in BASE_CLASSES.md

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2024 Peter Hinch

class BlockDevice:
    def __init__(self, nbits, nchips, chip_size):
        self._c_bytes = chip_size  # Size of chip in bytes
        self._a_bytes = chip_size * nchips  # Size of array
        self._nbits = nbits  # Block size in bits
        self._block_size = 2 ** nbits
        self._rwbuf = bytearray(1)

    def __len__(self):
        return self._a_bytes

    def __setitem__(self, addr, value):
        if isinstance(addr, slice):
            return self._wslice(addr, value)
        self._rwbuf[0] = value
        self.readwrite(addr, self._rwbuf, False)

    def __getitem__(self, addr):
        if isinstance(addr, slice):
            return self._rslice(addr)
        return self.readwrite(addr, self._rwbuf, True)[0]

    # Handle special cases of a slice. Always return a pair of positive indices.
    def _do_slice(self, addr):
        if not (addr.step is None or addr.step == 1):
            raise NotImplementedError(
                "only slices with step=1 (aka None) are supported")
        start = addr.start if addr.start is not None else 0
        stop = addr.stop if addr.stop is not None else self._a_bytes
        start = start if start >= 0 else self._a_bytes + start
        stop = stop if stop >= 0 else self._a_bytes + stop
        return start, stop

    def _wslice(self, addr, value):
        start, stop = self._do_slice(addr)
        try:
            if len(value) == (stop - start):
                res = self.readwrite(start, value, False)
            else:
                raise RuntimeError("Slice must have same length as data")
        except TypeError:
            raise RuntimeError("Can only assign bytes/bytearray to a slice")
        return res

    def _rslice(self, addr):
        start, stop = self._do_slice(addr)
        buf = bytearray(stop - start)
        return self.readwrite(start, buf, True)

    # IOCTL protocol.
    def sync(self):  # Nothing to do for unbuffered devices. Subclass overrides.
        return

    def readblocks(self, blocknum, buf, offset=0):
        self.readwrite(offset + (blocknum << self._nbits), buf, True)

    def writeblocks(self, blocknum, buf, offset=0):
        self.readwrite(offset + (blocknum << self._nbits), buf, False)


# Hardware agnostic base class for EEPROM arrays
class EepromDevice(BlockDevice):
    def __init__(self, nbits, nchips, chip_size, page_size, verbose):
        super().__init__(nbits, nchips, chip_size)
        # Handle page size arg
        if page_size not in (None, 16, 32, 64, 128, 256):
            raise ValueError(f"Invalid page size: {page_size}")
        self._set_pagesize(page_size)  # Set page size
        verbose and print("Page size:", self._page_size)

    def _psize(self, ps):  # Set page size and page mask
        self._page_size = ps
        self._page_mask = ~(ps - 1)

    def get_page_size(self):  # For test script
        return self._page_size

    # Measuring page size should not be done in production code. See docs.
    def _set_pagesize(self, page_size):
        if page_size is None:  # Measure it.
            self._psize(16)  # Conservative
            old = self[:129]  # Save old contents (nonvolatile!)
            self._psize(256)  # Ambitious
            r = (16, 32, 64, 128)  # Legal page sizes + 256
            for x in r:
                self[x] = 255  # Write single bytes, don't invoke page write
            # Zero 129 bytes attempting to use 256 byte pages
            self[0:129] = b"\0" * 129
            try:
                ps = next(z for z in r if self[z])
            except StopIteration:
                ps = 256
            self._psize(ps)
            self[:129] = old
        else:  # Validated page_size was supplied
            self._psize(page_size)
