"""Arithmetic encoder/decoder module (LARC) - using exact C tables for binary compatibility."""

import re

ARENTRIES = 4096
ACCUMSIZE = 13
ACCUMMASK = 8191
DELAYREGSIZE = 24
DELAYREGMASK = 0x00FFFFFF
PPBUFSIZ = 2048


def _parse_c_array(content: str, array_name: str) -> list:
    """Parse a C array from header file content."""
    pattern = rf"int {array_name}\[ARENTRIES\] = \{{(.*?)}};"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find {array_name} in C tables")

    nums = re.findall(r"\d+", match.group(1))
    return [int(n) for n in nums]


with open("/home/dclavijo/my_code/daedalus-repos/ctw/ctwlarc-tables.h") as f:
    c_content = f.read()

ARexp = _parse_c_array(c_content, "ARexp")
ARlog = _parse_c_array(c_content, "ARlog")


class ArithmeticEncoder:
    """Arithmetic encoder - exact C implementation."""

    def __init__(self):
        self.file = None
        self.delayreg = 0
        self.accum = 0
        self.intpntr = 0
        self._pu_slack = 0
        self._notpu_edbits = 8
        self._notpu_edbytes = PPBUFSIZ
        self._pu_edbufs = 0
        self._pu_buf = bytearray(PPBUFSIZ)
        self._skipbits = DELAYREGSIZE

    def init(self, outfile) -> None:
        self.file = outfile
        self.delayreg = 0
        self.accum = 0
        self.intpntr = 0
        self._pu_slack = 0
        self._notpu_edbits = 8
        self._notpu_edbytes = PPBUFSIZ
        self._pu_edbufs = 0
        self._pu_buf = bytearray(PPBUFSIZ)
        self._skipbits = DELAYREGSIZE

    def _pushbit(self, bit: bool) -> None:
        if self._skipbits:
            self._skipbits -= 1
        else:
            if bit:
                self._pu_slack = (self._pu_slack << 1) | 1
            else:
                self._pu_slack <<= 1
            self._notpu_edbits -= 1
            if self._notpu_edbits == 0:
                self._pu_buf[PPBUFSIZ - self._notpu_edbytes] = self._pu_slack & 0xFF
                self._notpu_edbytes -= 1
                if self._notpu_edbytes == 0:
                    self.file.write(self._pu_buf)
                    self._pu_edbufs += 1
                    self._notpu_edbytes = PPBUFSIZ
                self._notpu_edbits = 8
                self._pu_slack = 0

    def _pushblk(self, blk: int, bitsinblk: int) -> None:
        if self._skipbits:
            if bitsinblk <= self._skipbits:
                self._skipbits -= bitsinblk
                return
            else:
                bitsinblk -= self._skipbits
                self._skipbits = 0

        self._pu_slack = (self._pu_slack << bitsinblk) | blk
        self._notpu_edbits -= bitsinblk

        while self._notpu_edbits <= 0:
            byt = self._pu_slack >> (-self._notpu_edbits)
            self._pu_buf[PPBUFSIZ - self._notpu_edbytes] = byt
            self._notpu_edbytes -= 1
            if self._notpu_edbytes == 0:
                self.file.write(self._pu_buf)
                self._pu_edbufs += 1
                self._notpu_edbytes = PPBUFSIZ
            self._pu_slack ^= byt << (-self._notpu_edbits)
            self._notpu_edbits += 8

    def _pushexit(self) -> None:
        if self._notpu_edbits < 8:
            self._pu_buf[PPBUFSIZ - self._notpu_edbytes] = (
                self._pu_slack << self._notpu_edbits
            ) & 0xFF
            self._notpu_edbytes -= 1
            self._notpu_edbits += 8

        self.file.write(self._pu_buf[: PPBUFSIZ - self._notpu_edbytes])

    def encode(self, instep: int, symbsmall: bool) -> None:
        if self.intpntr >= ARENTRIES:
            shifts = self.intpntr // ARENTRIES

            blk = self.accum >> (ACCUMSIZE - shifts)
            self.accum = (self.accum << shifts) & ACCUMMASK
            self._pushblk(self.delayreg >> (DELAYREGSIZE - shifts), shifts)
            self.delayreg = ((self.delayreg << shifts) & DELAYREGMASK) | blk

            self.intpntr -= shifts * ARENTRIES

        while self.delayreg == DELAYREGMASK:
            bit = self.accum >> (ACCUMSIZE - 1)
            self.accum = (self.accum << 1) & ACCUMMASK
            self._pushbit((self.delayreg >> (DELAYREGSIZE - 1)) != 0)
            self.delayreg = ((self.delayreg << 1) & DELAYREGMASK) | bit

        bigpntr = self.intpntr + instep
        if symbsmall:
            if bigpntr < ARENTRIES:
                self.accum += 2 * ARexp[bigpntr]
                if self.accum > ACCUMMASK:
                    self.accum &= ACCUMMASK
                    self.delayreg += 1
                self.intpntr = ARlog[ARexp[self.intpntr] - ARexp[bigpntr]]
            else:
                bigpntr -= ARENTRIES
                self.accum += ARexp[bigpntr]
                if self.accum > ACCUMMASK:
                    self.accum &= ACCUMMASK
                    self.delayreg += 1
                self.intpntr = (
                    ARlog[2 * ARexp[self.intpntr] - ARexp[bigpntr]] + ARENTRIES
                )
        else:
            self.intpntr = bigpntr

    def exit(self) -> int:
        self._pushblk(self.delayreg, DELAYREGSIZE)
        self._pushblk(self.accum, ACCUMSIZE)
        codelength = (
            self._pu_edbufs * PPBUFSIZ + PPBUFSIZ - self._notpu_edbytes
        ) * 8 + (8 - self._notpu_edbits)
        self._pushexit()
        return codelength


class ArithmeticDecoder:
    """Arithmetic decoder - exact C implementation."""

    def __init__(self):
        self.file = None
        self.accum = 0
        self.intpntr = 0
        self._pu_slack = 0
        self._notpu_edbits = 0
        self._notpu_edbytes = 0
        self._pu_edbufs = 0
        self._pu_buf = bytearray(PPBUFSIZ)
        self.codaccum = 0
        self.delayreg = 0
        self.codelayreg = 0

    def init(self, infile) -> None:
        self.file = infile
        self.accum = 0
        self.intpntr = 0
        self._pu_slack = 0
        self._notpu_edbits = 0
        self._notpu_edbytes = 0
        self._pu_edbufs = 0
        self._pu_buf = bytearray(PPBUFSIZ)
        self.codaccum = self._pullblk(ACCUMSIZE)
        self.delayreg = 0
        self.codelayreg = 0

    def _pullbit(self) -> bool:
        if self._notpu_edbits == 0:
            if self._notpu_edbytes == 0:
                data = self.file.read(PPBUFSIZ)
                if not data:
                    self._pu_buf = bytearray(PPBUFSIZ)
                else:
                    self._pu_buf = bytearray(data)
                self._notpu_edbytes = len(self._pu_buf)
                self._pu_edbufs += 1

            self._notpu_edbytes -= 1
            self._pu_slack = self._pu_buf[len(self._pu_buf) - self._notpu_edbytes - 1]
            self._notpu_edbits = 8

        self._notpu_edbits -= 1
        bit = (self._pu_slack >> self._notpu_edbits) & 1
        self._pu_slack ^= bit << self._notpu_edbits
        return bool(bit)

    def _pullblk(self, bitsinblk: int) -> int:
        self._notpu_edbits -= bitsinblk
        while self._notpu_edbits < 0:
            if self._notpu_edbytes == 0:
                data = self.file.read(PPBUFSIZ)
                if not data:
                    self._pu_buf = bytearray(PPBUFSIZ)
                else:
                    self._pu_buf = bytearray(data)
                self._notpu_edbytes = len(self._pu_buf)
                self._pu_edbufs += 1

            self._pu_slack = (self._pu_slack << 8) | self._pu_buf[
                len(self._pu_buf) - self._notpu_edbytes
            ]
            self._notpu_edbytes -= 1
            self._notpu_edbits += 8

        blk = self._pu_slack >> self._notpu_edbits
        self._pu_slack ^= blk << self._notpu_edbits
        return blk

    def decode(self, instep: int) -> bool:
        shifts = 0
        if self.intpntr >= ARENTRIES:
            shifts = self.intpntr // ARENTRIES

            blk = self.accum >> (ACCUMSIZE - shifts)
            self.accum = (self.accum << shifts) & ACCUMMASK
            self.delayreg = ((self.delayreg << shifts) & DELAYREGMASK) | blk

            codblk = self.codaccum >> (ACCUMSIZE - shifts)
            self.codaccum = ((self.codaccum << shifts) & ACCUMMASK) | self._pullblk(
                shifts
            )
            self.codelayreg = ((self.codelayreg << shifts) & DELAYREGMASK) | codblk

            self.intpntr -= shifts * ARENTRIES

        while self.delayreg == DELAYREGMASK:
            bit = self.accum >> (ACCUMSIZE - 1)
            self.accum = (self.accum << 1) & ACCUMMASK
            self.delayreg = ((self.delayreg << 1) & DELAYREGMASK) | bit

            codbit = self.codaccum >> (ACCUMSIZE - 1)
            self.codaccum = ((self.codaccum << 1) & ACCUMMASK) | self._pullbit()
            self.codelayreg = ((self.codelayreg << 1) & DELAYREGMASK) | codbit

        bigpntr = self.intpntr + instep

        if bigpntr < ARENTRIES:
            thraccum = self.accum + 2 * ARexp[bigpntr]
            thrdelayreg = self.delayreg

            if thraccum > ACCUMMASK:
                thraccum &= ACCUMMASK
                thrdelayreg += 1

            symbsmall = (self.codelayreg > thrdelayreg) or (
                (self.codelayreg == thrdelayreg) and (self.codaccum >= thraccum)
            )

            if symbsmall:
                self.accum = thraccum
                self.delayreg = thrdelayreg
                self.intpntr = ARlog[ARexp[self.intpntr] - ARexp[bigpntr]]
            else:
                self.intpntr = bigpntr
        else:
            bigpntr -= ARENTRIES
            thraccum = self.accum + ARexp[bigpntr]
            thrdelayreg = self.delayreg

            if thraccum > ACCUMMASK:
                thraccum &= ACCUMMASK
                thrdelayreg += 1

            symbsmall = (self.codelayreg > thrdelayreg) or (
                (self.codelayreg == thrdelayreg) and (self.codaccum >= thraccum)
            )

            if symbsmall:
                self.accum = thraccum
                self.delayreg = thrdelayreg
                self.intpntr = (
                    ARlog[2 * ARexp[self.intpntr] - ARexp[bigpntr]] + ARENTRIES
                )
            else:
                self.intpntr = bigpntr + ARENTRIES

        return symbsmall


STEPHALF = ARENTRIES
