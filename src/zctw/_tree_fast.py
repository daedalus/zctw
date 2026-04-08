"""Optimized CTW tree management using numpy arrays.

This module provides an optimized version of the CTW tree structure
using numpy arrays for faster memory access and operations.
"""

import numpy as np

from zctw.settings import MAX_TREEDEPTH, CTWSettings

EMPTY_NODE = 0xFFFFFFFF


SHIFT_MASK = np.array([0x00, 0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE], dtype=np.uint8)


TPERM = np.array(
    (
        175715,
        11428377,
        6429025,
        1663333,
        23160013,
        23383373,
        13454579,
        21820291,
        15958541,
        25300137,
        829939,
        11137997,
        32754777,
        30169415,
        5850653,
        21372299,
        1936299,
        25930603,
        28011331,
        23806635,
        21146549,
        11252897,
        28614785,
        10519007,
        8511025,
        31338949,
        3261913,
        29743389,
        31005773,
        18632081,
        5083357,
        26271075,
        14508753,
        23253199,
        13684507,
        13573115,
        18611199,
        33291877,
        33449115,
        6593227,
        10144419,
        13279781,
        10626139,
        2382529,
        5947455,
        12599229,
        4176947,
        29110999,
        3331965,
        14122125,
        24939693,
        9219547,
        11394017,
        31187013,
        31474833,
        4493797,
        9561129,
        31730093,
        2731497,
        28174791,
        32098091,
        29830103,
        19650243,
        30852053,
        12833907,
        30700077,
        7482489,
        2914805,
        7992485,
        32810335,
        10837921,
        23044107,
        27265791,
        720783,
        16748255,
        26140285,
        14581007,
        8196081,
        17822045,
        32595283,
        22893479,
        22259317,
        27686021,
        7636277,
        8729813,
        20239751,
        13993963,
        25684823,
        32200227,
        22422391,
        2324333,
        24604007,
        23946753,
        23462375,
        124681,
        31918193,
        17330473,
        7415959,
        19437313,
        9896203,
        16845629,
        17513673,
        20760837,
        13174013,
        17104055,
        16561691,
        11934515,
        1782765,
        20180401,
        32354743,
        28423919,
        28765833,
        15632831,
        9027229,
        29269159,
        10266289,
        10924435,
        11637447,
        26396405,
        13038615,
        15996601,
        1488961,
        12075281,
        4264165,
        17884265,
        14968853,
        6821141,
        1381437,
        18103393,
        3957103,
        6385465,
        24066119,
        20465275,
        4618805,
        8008991,
        3481237,
        18781687,
        9828029,
        32947459,
        12387141,
        16991359,
        21266225,
        8335701,
        20009999,
        22286055,
        976719,
        15159267,
        22012829,
        31693831,
        27002669,
        470127,
        19689079,
        7239471,
        7811001,
        19904693,
        28882027,
        11823663,
        6958855,
        3081979,
        17234779,
        16472607,
        22683613,
        2088095,
        31235775,
        10403507,
        12497441,
        11673811,
        2151187,
        13833155,
        18072513,
        29606323,
        29471553,
        28524619,
        20990711,
        4912877,
        16182419,
        15503877,
        9569595,
        342621,
        20602089,
        6088723,
        15209251,
        1254157,
        19074505,
        17680799,
        29990825,
        27240853,
        27891119,
        26586763,
        28216267,
        9161271,
        30029689,
        3635335,
        24676089,
        8845649,
        16339449,
        22149205,
        33051657,
        5507131,
        539353,
        3856427,
        14167023,
        2879015,
        32384923,
        2595407,
        26890135,
        5216211,
        26726993,
        30560629,
        5338407,
        24455053,
        19369345,
        26050871,
        25245251,
        20333385,
        4409727,
        21593797,
        25085337,
        12949835,
        26823529,
        21719275,
        23653017,
        15374617,
        10033225,
        18368933,
        4826457,
        27613267,
        22565485,
        5401919,
        7159313,
        20844915,
        1143761,
        24367331,
        30466953,
        14911951,
        25808479,
        30301989,
        6235377,
        19198055,
        15754883,
        6718009,
        8534305,
        3744253,
        19004859,
        33405627,
        29014907,
        12286853,
        24872215,
        25499361,
        18276439,
        14702223,
        5672667,
        9362289,
        14381475,
        24224259,
        27394735,
    ),
    dtype=np.int32,
)


def _hash1(c: int, mask: int) -> int:
    """Hash function for tree index."""
    return TPERM[c] & mask


def _cptrtoi(p: int) -> int:
    """Get index from symbol pointer."""
    return p & 0x00FFFFFF


def _itocptr(i: int, nrtries: int, phase: int) -> int:
    """Convert index, nrtries, phase to symbol pointer."""
    return ((((nrtries - 1) << 3) | phase) << 24) | (i & 0x00FFFFFF)


def byte_prefix(b: int, f: int) -> int:
    """Get bits in b at the left side of bit f."""
    return b & SHIFT_MASK[f]


def byte_bit(b: int, f: int) -> int:
    """Get bit f in byte b."""
    return (b >> (7 - f)) & 1


class CTWTreeOptimized:
    """Optimized CTW tree using numpy arrays."""

    __slots__ = (
        "settings",
        "filebuffer",
        "tree_symbol",
        "tree_cnt0",
        "tree_cnt1",
        "tree_logbeta",
        "nrnodes",
        "nrsymbols",
        "nrfailed",
        "rootindex",
        "localindex",
        "localdepth",
        "_ctxstring",
        "_mask",
        "_treedepth_plus1",
    )

    def __init__(self, settings: CTWSettings):
        self.settings = settings
        self.filebuffer: np.ndarray | None = None
        self.tree_symbol: np.ndarray | None = None
        self.tree_cnt0: np.ndarray | None = None
        self.tree_cnt1: np.ndarray | None = None
        self.tree_logbeta: np.ndarray | None = None
        self.nrnodes: int = 0
        self.nrsymbols: int = 0
        self.nrfailed: int = 0
        self.rootindex = np.zeros(8, dtype=np.int32)
        self.localindex = np.zeros(MAX_TREEDEPTH + 1, dtype=np.int32)
        self.localdepth: int = 0
        self._ctxstring = np.zeros(MAX_TREEDEPTH + 2, dtype=np.int32)
        self._mask: int = 0
        self._treedepth_plus1: int = 0

    def tree_frozen(self) -> bool:
        """Check if tree is frozen."""
        return self.nrsymbols >= self.settings.filebufsize

    def init_filebuffer(self, databytes: int) -> bool:
        """Allocate file buffer."""
        size = min(self.settings.filebufsize, databytes)
        self.filebuffer = np.zeros(size, dtype=np.uint8)
        return True

    def init_tree(self, sym: int) -> bool:
        """Initialize tree structure with numpy arrays."""
        max_nodes = self.settings.maxnrnodes
        self._mask = max_nodes - 1
        self._treedepth_plus1 = self.settings.treedepth + 1

        self.tree_symbol = np.full(max_nodes, EMPTY_NODE, dtype=np.uint32)
        self.tree_cnt0 = np.zeros(max_nodes, dtype=np.int32)
        self.tree_cnt1 = np.zeros(max_nodes, dtype=np.int32)
        self.tree_logbeta = np.zeros(max_nodes, dtype=np.int32)

        for f in range(8):
            i = _hash1(f, self._mask)
            self.rootindex[f] = i
            self.tree_symbol[i] = _itocptr(self.settings.treedepth + 2, 1, f)
            if byte_bit(sym, f) == 0:
                self.tree_cnt0[i] = 1
            else:
                self.tree_cnt1[i] = 1

        self.nrnodes = 8
        self.nrfailed = 0
        return True

    def _find_index(
        self, phase: int, curindex: int, ctxdepth: int, ctxstring: np.ndarray
    ) -> tuple[int, int]:
        """Find child node in tree."""
        fb = self.filebuffer
        ts = self.tree_symbol
        mask = self._mask
        maxnrtries = self.settings.maxnrtries

        offset = _hash1(int(ctxstring[ctxdepth - 1]), mask) ^ ((phase + 1) << 1)

        for nrtries in range(1, maxnrtries + 1):
            curindex = (curindex + offset) & mask

            if ts[curindex] == EMPTY_NODE:
                if self.nrsymbols >= self.settings.filebufsize:
                    return -1, curindex
                return nrtries, curindex

            stored_info = ts[curindex] >> 24
            if (((nrtries - 1) << 3) | phase) == stored_info:
                ptr = _cptrtoi(ts[curindex])
                if ctxdepth == 1:
                    s = fb[ptr] & SHIFT_MASK[phase]
                else:
                    s = fb[ptr]

                if ctxstring[ctxdepth - 1] == s:
                    return 0, curindex

        self.nrfailed += 1
        return -1, 0

    def _find_or_create_old_leaf(
        self, phase: int, curindex: int, depth: int, ctxstring: np.ndarray, context: int
    ) -> None:
        """Find or create old leaf node."""
        ts = self.tree_symbol
        result, oldindex = self._find_index(phase, curindex, depth, ctxstring)

        if result > 0:
            ts[oldindex] = _itocptr(context, result, phase)
            self.tree_cnt0[oldindex] = self.tree_cnt0[curindex]
            self.tree_cnt1[oldindex] = self.tree_cnt1[curindex]
            self.tree_logbeta[oldindex] = self.tree_logbeta[curindex]
            self.nrnodes += 1

    def update_path(self, newinfo: list) -> None:
        """Update nodes in path."""
        li = self.localindex
        tc0 = self.tree_cnt0
        tc1 = self.tree_cnt1
        tlb = self.tree_logbeta
        depth = self.localdepth

        while depth > 0:
            depth -= 1
            cnt0, cnt1, logbeta = newinfo[depth]
            idx = li[depth]
            tc0[idx] = cnt0
            tc1[idx] = cnt1
            tlb[idx] = logbeta

    def find_path(
        self, phase: int, context: int, ctxstring: np.ndarray, curdepth: list
    ) -> list:
        """Find path in CTW tree."""
        fb = self.filebuffer
        ts = self.tree_symbol
        tc0 = self.tree_cnt0
        tc1 = self.tree_cnt1
        tlb = self.tree_logbeta
        li = self.localindex
        treedepth_plus1 = self._treedepth_plus1
        treedepth_plus2 = treedepth_plus1 + 1
        strictpruning = self.settings.strictpruning
        maxnrtries = self.settings.maxnrtries

        depth = 0
        curindex = self.rootindex[phase]
        ctwinfo = []
        td = treedepth_plus2

        while True:
            li[depth] = curindex
            ctwinfo.append((tc0[curindex], tc1[curindex], tlb[curindex]))

            if depth == treedepth_plus1:
                self.localdepth = td
                curdepth[0] = td
                return ctwinfo

            depth += 1
            context -= 1

            result, newindex = self._find_index(phase, curindex, depth, ctxstring)

            if result == -1:
                self.localdepth = depth
                curdepth[0] = depth
                return ctwinfo
            elif result == 0:
                curindex = newindex
            else:
                while True:
                    previndex = _cptrtoi(ts[curindex]) - 1

                    if strictpruning and previndex != (context + 1):
                        same = True
                        for d in range(depth, treedepth_plus2):
                            if d == 1:
                                oldsym = fb[previndex + depth - d] & SHIFT_MASK[phase]
                            else:
                                oldsym = fb[previndex + depth - d]
                            if oldsym != ctxstring[d - 1]:
                                same = False
                                break
                        if same:
                            self.localdepth = depth
                            curdepth[0] = depth
                            return ctwinfo

                    ts[newindex] = _itocptr(context + 1, result, phase)
                    self.nrnodes += 1
                    li[depth] = newindex
                    ctwinfo.append((0, 0, 0))

                    newsym = ctxstring[depth - 1]
                    if depth == 1:
                        oldsym = fb[previndex] & SHIFT_MASK[phase]
                    else:
                        oldsym = fb[previndex]

                    if oldsym == newsym:
                        ts[newindex] = _itocptr(previndex, result, phase)
                        tc0[newindex] = tc0[curindex]
                        tc1[newindex] = tc1[curindex]
                        tlb[newindex] = tlb[curindex]
                        curindex = newindex
                        ctwinfo[depth] = (tc0[curindex], tc1[curindex], tlb[curindex])
                    else:
                        ctxstring[depth - 1] = oldsym
                        self._find_or_create_old_leaf(
                            phase, curindex, depth, ctxstring, previndex
                        )
                        ctxstring[depth - 1] = newsym
                        self.localdepth = depth + 1
                        curdepth[0] = depth + 1
                        return ctwinfo

                    if depth == treedepth_plus1:
                        self.localdepth = td
                        curdepth[0] = td
                        return ctwinfo

                    depth += 1
                    context -= 1
                    result, newindex = self._find_index(
                        phase, curindex, depth, ctxstring
                    )

                    if result == -1:
                        newsym = ctxstring[depth - 1]
                        previndex = _cptrtoi(ts[curindex]) - 1
                        oldsym = fb[previndex]
                        ctxstring[depth - 1] = oldsym
                        if oldsym != newsym:
                            self._find_or_create_old_leaf(
                                phase, curindex, depth, ctxstring, previndex
                            )
                        ctxstring[depth - 1] = newsym
                        self.localdepth = depth
                        curdepth[0] = depth
                        return ctwinfo
                    elif result == 0:
                        curindex = newindex

    def init_ctxstring(self) -> None:
        """Initialize context string."""
        fb = self.filebuffer
        td = self.settings.treedepth
        cs = self._ctxstring
        for d in range(td + 1):
            cs[d + 1] = fb[td + 1 - d]

    def get_ctxstring(self) -> np.ndarray:
        return self._ctxstring

    def set_ctxstring(self, ctxstring) -> None:
        self._ctxstring[:] = ctxstring[:]

    def free_memory(self) -> None:
        """Free allocated memory."""
        self.filebuffer = None
        self.tree_symbol = None
        self.tree_cnt0 = None
        self.tree_cnt1 = None
        self.tree_logbeta = None
