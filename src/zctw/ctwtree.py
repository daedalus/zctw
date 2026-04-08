"""Context Tree Weighting tree management module.

This module handles finding and updating paths in the CTW trees and managing
the array containing the data of the CTW trees.

Uses flat arrays like the C implementation for performance.
"""

from zctw.settings import MAX_TREEDEPTH, CTWSettings

EMPTY_NODE = 0xFFFFFFFF


SHIFT_MASK = (0x00, 0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE)


def byte_prefix(b: int, f: int) -> int:
    """Get bits in b at the left side of bit f."""
    return b & SHIFT_MASK[f]


def byte_bit(b: int, f: int) -> int:
    """Get bit f in byte b."""
    return (b >> (7 - f)) & 1


TPERM = (
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
)


def _hash1(c: int, maxnrnodes: int) -> int:
    """Hash function for tree index."""
    return TPERM[c] & (maxnrnodes - 1)


def _itocptr(i: int, nrtries: int, phase: int) -> int:
    """Convert index, nrtries, phase to symbol pointer."""
    return ((((nrtries - 1) << 3) | phase) << 24) | i


def _cptrtoi(p: int) -> int:
    """Get index in filebuffer from symbol pointer."""
    return p & 0x00FFFFFF


class CTWTree:
    """CTW tree structure manager using flat arrays for performance."""

    __slots__ = (
        "settings",
        "filebuffer",
        "tree_symbol",
        "tree_cnt0",
        "tree_cnt1",
        "tree_logbeta",
        "maxnrnodes",
        "nrnodes",
        "nrsymbols",
        "nrfailed",
        "rootindex",
        "localindex",
        "localdepth",
        "_ctxstring",
        "_mask",
    )

    def __init__(self, settings: CTWSettings):
        self.settings = settings
        self.filebuffer: bytearray | None = None
        self.tree_symbol: list[int] | None = None
        self.tree_cnt0: list[int] | None = None
        self.tree_cnt1: list[int] | None = None
        self.tree_logbeta: list[int] | None = None
        self.maxnrnodes: int = 0
        self.nrnodes: int = 0
        self.nrsymbols: int = 0
        self.nrfailed: int = 0
        self.rootindex = [0] * 8
        self.localindex = [0] * (MAX_TREEDEPTH + 1)
        self.localdepth: int = 0
        self._ctxstring = [0] * (MAX_TREEDEPTH + 2)
        self._mask: int = 0

    def tree_frozen(self) -> bool:
        """Check if tree structure is frozen."""
        return self.nrsymbols >= self.settings.filebufsize

    def init_filebuffer(self, databytes: int) -> bool:
        """Allocate file buffer (no longer called during encode for lazy allocation)."""
        if self.filebuffer is None:
            size = min(self.settings.filebufsize, databytes)
            self.filebuffer = bytearray(size)
        return True

    def _ensure_tree_allocated(self) -> bool:
        """Lazy tree allocation - only allocate when first needed."""
        if self.tree_symbol is not None:
            return True

        max_nodes = self.settings.maxnrnodes
        self.maxnrnodes = max_nodes
        self._mask = max_nodes - 1

        self.tree_symbol = [EMPTY_NODE] * max_nodes
        self.tree_cnt0 = [0] * max_nodes
        self.tree_cnt1 = [0] * max_nodes
        self.tree_logbeta = [0] * max_nodes

        self.nrnodes = 0
        self.nrfailed = 0
        return True

    def _ensure_filebuffer_allocated(self, databytes: int) -> None:
        """Lazy filebuffer allocation."""
        if self.filebuffer is None:
            size = min(self.settings.filebufsize, databytes)
            self.filebuffer = bytearray(size)

    def init_tree(self, sym: int) -> bool:
        """Initialize tree structure with flat arrays (like C)."""
        self._ensure_tree_allocated()
        max_nodes = self.settings.maxnrnodes

        for f in range(8):
            i = _hash1(f, max_nodes)
            self.rootindex[f] = i
            self.tree_symbol[i] = _itocptr(self.settings.treedepth + 2, 1, f)
            if byte_bit(sym, f) == 0:
                self.tree_cnt0[i] = 1
            else:
                self.tree_cnt1[i] = 1

        self.nrnodes = 8
        self.nrfailed = 0
        return True

    def _get_node(self, index: int) -> tuple[int, int, int, int]:
        """Get node data at index."""
        return (
            self.tree_symbol[index],
            self.tree_cnt0[index],
            self.tree_cnt1[index],
            self.tree_logbeta[index],
        )

    def _set_node(self, index: int, cnt0: int, cnt1: int, logbeta: int) -> None:
        """Set node data at index."""
        self.tree_cnt0[index] = cnt0
        self.tree_cnt1[index] = cnt1
        self.tree_logbeta[index] = logbeta

    def _copy_node(self, dst: int, src: int) -> None:
        """Copy node data from src to dst."""
        self.tree_cnt0[dst] = self.tree_cnt0[src]
        self.tree_cnt1[dst] = self.tree_cnt1[src]
        self.tree_logbeta[dst] = self.tree_logbeta[src]

    def _find_index(
        self, phase: int, curindex: int, ctxdepth: int, ctxstring: list
    ) -> tuple[int, int]:
        """Find child node in tree.

        Returns:
            (result, newindex): result >= 1 means new node, 0 means old node, -1 means failure
        """
        tree_symbol = self.tree_symbol
        filebuffer = self.filebuffer
        maxnrnodes = self.maxnrnodes
        mask = self._mask
        maxnrtries = self.settings.maxnrtries
        SHIFT_MASK = (0x00, 0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE)

        offset = _hash1(ctxstring[ctxdepth - 1], maxnrnodes) ^ ((phase + 1) << 1)

        for nrtries in range(1, maxnrtries + 1):
            curindex = (curindex + offset) & mask

            sym = tree_symbol[curindex]
            if sym == EMPTY_NODE:
                if self.nrsymbols >= self.settings.filebufsize:
                    return -1, curindex
                return nrtries, curindex

            stored_info = sym >> 24
            if ((nrtries - 1) * 8 | phase) == stored_info:
                idx = sym & 0x00FFFFFF
                if ctxdepth == 1:
                    s = filebuffer[idx] & SHIFT_MASK[phase]
                else:
                    s = filebuffer[idx]

                if ctxstring[ctxdepth - 1] == s:
                    return 0, curindex

        self.nrfailed += 1
        return -1, 0

    def _find_or_create_old_leaf(
        self, phase: int, curindex: int, depth: int, ctxstring: list, context: int
    ) -> None:
        """Find or create an old leaf node."""
        result, oldindex = self._find_index(phase, curindex, depth, ctxstring)

        if result > 0:
            self.tree_symbol[oldindex] = _itocptr(context, result, phase)
            self._copy_node(oldindex, curindex)
            self.nrnodes += 1

    def update_path(self, newinfo: list[tuple[int, int, int]]) -> None:
        """Update nodes in path with new info."""
        depth = self.localdepth
        while depth > 0:
            depth -= 1
            cnt0, cnt1, logbeta = newinfo[depth]
            self._set_node(self.localindex[depth], cnt0, cnt1, logbeta)

    def find_path(
        self, phase: int, context: int, ctxstring: list, curdepth: list
    ) -> list[tuple[int, int, int]]:
        """Find path in CTW tree and return CTW info on path."""
        if self.tree_symbol is None:
            self._ensure_tree_allocated()
            max_nodes = self.settings.maxnrnodes
            self.maxnrnodes = max_nodes
            self._mask = max_nodes - 1
            self.tree_symbol = [EMPTY_NODE] * max_nodes
            self.tree_cnt0 = [0] * max_nodes
            self.tree_cnt1 = [0] * max_nodes
            self.tree_logbeta = [0] * max_nodes
            self.nrnodes = 0
            self.nrfailed = 0

        tree_symbol = self.tree_symbol
        tree_cnt0 = self.tree_cnt0
        tree_cnt1 = self.tree_cnt1
        tree_logbeta = self.tree_logbeta
        filebuffer = self.filebuffer
        localindex = self.localindex
        rootindex = self.rootindex
        maxnrnodes = self.maxnrnodes
        mask = self._mask
        treedepth = self.settings.treedepth
        treedepth_plus1 = treedepth + 1
        treedepth_plus2 = treedepth + 2
        maxnrtries = self.settings.maxnrtries
        filebufsize = self.settings.filebufsize
        strictpruning = self.settings.strictpruning
        SHIFT_MASK = (0x00, 0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE)

        depth = 0
        curindex = rootindex[phase]
        ctwinfo: list[tuple[int, int, int]] = []

        while True:
            localindex[depth] = curindex
            ctwinfo.append(
                (tree_cnt0[curindex], tree_cnt1[curindex], tree_logbeta[curindex])
            )

            if depth == treedepth_plus1:
                self.localdepth = treedepth_plus2
                curdepth[0] = self.localdepth
                return ctwinfo

            depth += 1
            context -= 1

            offset = _hash1(ctxstring[depth - 1], maxnrnodes) ^ ((phase + 1) << 1)

            for nrtries in range(1, maxnrtries + 1):
                curindex = (curindex + offset) & mask

                sym = tree_symbol[curindex]
                if sym == EMPTY_NODE:
                    if self.nrsymbols >= filebufsize:
                        self.localdepth = depth
                        curdepth[0] = depth
                        return ctwinfo
                    nrtries_result = nrtries
                    newindex_result = curindex
                    break

                stored_info = sym >> 24
                if ((nrtries - 1) * 8 | phase) == stored_info:
                    idx = sym & 0x00FFFFFF
                    if idx < len(filebuffer):
                        if depth == 1:
                            s = filebuffer[idx] & SHIFT_MASK[phase]
                        else:
                            s = filebuffer[idx]

                        if ctxstring[depth - 1] == s:
                            nrtries_result = 0
                            newindex_result = curindex
                            break
            else:
                self.nrfailed += 1
                self.localdepth = depth
                curdepth[0] = depth
                return ctwinfo

            if nrtries_result == 0:
                continue

            newindex = newindex_result

            while True:
                previndex = (tree_symbol[curindex] & 0x00FFFFFF) - 1

                if strictpruning and previndex >= depth and previndex != (context + 1):
                    same = True
                    fb_len = len(filebuffer)
                    for d in range(depth, treedepth_plus2):
                        buf_idx = previndex + depth - d
                        if buf_idx < 0 or buf_idx >= fb_len:
                            same = False
                            break
                        if d == 1:
                            oldsym = filebuffer[buf_idx] & SHIFT_MASK[phase]
                        else:
                            oldsym = filebuffer[buf_idx]
                        if oldsym != ctxstring[d - 1]:
                            same = False
                            break
                    if same:
                        self.localdepth = depth
                        curdepth[0] = depth
                        return ctwinfo

                tree_symbol[newindex] = (((nrtries_result) << 3) | phase) << 24 | (
                    context + 1
                )
                self.nrnodes += 1
                localindex[depth] = newindex
                ctwinfo.append((0, 0, 0))

                newsym = ctxstring[depth - 1]
                if previndex >= 0 and previndex < len(filebuffer):
                    if depth == 1:
                        oldsym = filebuffer[previndex] & SHIFT_MASK[phase]
                    else:
                        oldsym = filebuffer[previndex]
                else:
                    oldsym = newsym

                if oldsym == newsym:
                    tree_symbol[newindex] = (
                        ((nrtries_result) << 3) | phase
                    ) << 24 | previndex
                    tree_cnt0[newindex] = tree_cnt0[curindex]
                    tree_cnt1[newindex] = tree_cnt1[curindex]
                    tree_logbeta[newindex] = tree_logbeta[curindex]
                    curindex = newindex
                    ctwinfo[depth] = (
                        tree_cnt0[curindex],
                        tree_cnt1[curindex],
                        tree_logbeta[curindex],
                    )
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
                    self.localdepth = treedepth_plus2
                    curdepth[0] = treedepth_plus2
                    return ctwinfo

                depth += 1
                context -= 1
                offset = _hash1(ctxstring[depth - 1], maxnrnodes) ^ ((phase + 1) << 1)

                for nrtries in range(1, maxnrtries + 1):
                    curindex = (curindex + offset) & mask

                    sym = tree_symbol[curindex]
                    if sym == EMPTY_NODE:
                        if self.nrsymbols >= filebufsize:
                            self.localdepth = depth
                            curdepth[0] = depth
                            return ctwinfo
                        nrtries_result = nrtries
                        newindex_result = curindex
                        break

                    stored_info = sym >> 24
                    if ((nrtries - 1) * 8 | phase) == stored_info:
                        idx = sym & 0x00FFFFFF
                        if idx < len(filebuffer):
                            if depth == 1:
                                s = filebuffer[idx] & SHIFT_MASK[phase]
                            else:
                                s = filebuffer[idx]

                            if ctxstring[depth - 1] == s:
                                nrtries_result = 0
                                newindex_result = curindex
                                break
                else:
                    self.nrfailed += 1
                    self.localdepth = depth
                    curdepth[0] = depth
                    return ctwinfo

                if nrtries_result == 0:
                    curindex = newindex_result
                else:
                    break

    def init_ctxstring(self) -> None:
        """Initialize context string from filebuffer."""
        for depth in range(self.settings.treedepth + 1):
            self._ctxstring[depth + 1] = self.filebuffer[
                self.settings.treedepth + 1 - depth
            ]

    def get_ctxstring(self) -> list:
        return self._ctxstring

    def set_ctxstring(self, ctxstring: list) -> None:
        self._ctxstring = ctxstring

    def free_memory(self) -> None:
        """Free allocated memory."""
        self.filebuffer = None
        self.tree_symbol = None
        self.tree_cnt0 = None
        self.tree_cnt1 = None
        self.tree_logbeta = None
