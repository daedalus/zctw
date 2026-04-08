"""CTW probability calculation module.

This module implements the mathematics of the CTW algorithm including
the zero-redundancy estimator and KT-estimator.
"""

from zctw.ctwmath import (
    ACCURACY,
    MAXCOUNTS,
    CTWjac,
    CTWlogar,
    CTWzlogpmax,
    CTWzlogpmin,
)
from zctw.settings import CTWSettings


class CTWProb:
    """CTW probability information."""

    __slots__ = ("logpwroot", "predsymb")

    def __init__(self, logpwroot: int = 0, predsymb: int = 0):
        self.logpwroot = logpwroot
        self.predsymb = predsymb


def ctw_data_from_one_count(bit: int) -> tuple[int, int, int]:
    """Create CTW data tuple with one count (cnt0, cnt1, logbeta)."""
    return (1 if bit == 0 else 0, 1 if bit == 1 else 0, 0)


def ctw_process(
    curdepth: int,
    ctwinfo: list[tuple[int, int, int]],
    ctwprob: CTWProb,
    dummy0info: list[tuple[int, int, int]],
    dummy1info: list[tuple[int, int, int]],
    settings: CTWSettings,
) -> None:
    """Process CTW tree to get weighted probability.

    Args:
        curdepth: Current depth in tree.
        ctwinfo: CTW info for each node on path (cnt0, cnt1, logbeta).
        ctwprob: Output probability structure.
        dummy0info: Output for dummy 0 update.
        dummy1info: Output for dummy 1 update.
        settings: CTW settings.
    """
    curdepth -= 1
    c0, c1, logbeta = ctwinfo[curdepth]

    if settings.use_zeroredundancy and (c1 == 0 or c0 == 0):
        if c1 == 0:
            loggamma = CTWzlogpmax[c0] - CTWzlogpmin[c0]
        else:
            loggamma = CTWzlogpmin[c1] - CTWzlogpmax[c1]
    else:
        loggamma = CTWlogar[2 * c0 + 1] - CTWlogar[2 * c1 + 1]

    if c0 == (MAXCOUNTS - 1):
        dummy0cnt0 = MAXCOUNTS // 2
        dummy0cnt1 = (c1 + 1) // 2
    else:
        dummy0cnt0 = c0 + 1
        dummy0cnt1 = c1

    if c1 == (MAXCOUNTS - 1):
        dummy1cnt0 = (c0 + 1) // 2
        dummy1cnt1 = MAXCOUNTS // 2
    else:
        dummy1cnt0 = c0
        dummy1cnt1 = c1 + 1

    dummy0info[curdepth] = (dummy0cnt0, dummy0cnt1, logbeta)
    dummy1info[curdepth] = (dummy1cnt0, dummy1cnt1, logbeta)

    if settings.rootweighting:
        enddepth = 0
    else:
        enddepth = 1

    while curdepth > enddepth:
        curdepth -= 1
        c0, c1, logbeta = ctwinfo[curdepth]

        if loggamma >= 0:
            logpw0 = -CTWjac(-loggamma)
            logpw1 = logpw0 - loggamma
        else:
            logpw1 = -CTWjac(loggamma)
            logpw0 = logpw1 + loggamma

        if settings.use_zeroredundancy and (c1 == 0 or c0 == 0):
            if c1 == 0:
                logpe0 = CTWzlogpmax[c0]
                logpe1 = CTWzlogpmin[c0]
            else:
                logpe0 = CTWzlogpmin[c1]
                logpe1 = CTWzlogpmax[c1]
        else:
            logcsumplusacc = CTWlogar[c0 + c1 + 1] + ACCURACY
            logpe0 = CTWlogar[2 * c0 + 1] - logcsumplusacc
            logpe1 = CTWlogar[2 * c1 + 1] - logcsumplusacc

        logbetatimespe0 = logbeta + logpe0
        diff0 = logbetatimespe0 - logpw0
        if diff0 >= 0:
            nom = logbetatimespe0 + CTWjac(-diff0)
        else:
            nom = logpw0 + CTWjac(diff0)

        logbetatimespe1 = logbeta + logpe1
        diff1 = logbetatimespe1 - logpw1
        if diff1 >= 0:
            den = logbetatimespe1 + CTWjac(-diff1)
        else:
            den = logpw1 + CTWjac(diff1)

        loggamma = nom - den

        if c0 == (MAXCOUNTS - 1):
            dummy0cnt0 = MAXCOUNTS // 2
            dummy0cnt1 = (c1 + 1) // 2
        else:
            dummy0cnt0 = c0 + 1
            dummy0cnt1 = c1

        if c1 == (MAXCOUNTS - 1):
            dummy1cnt0 = (c0 + 1) // 2
            dummy1cnt1 = MAXCOUNTS // 2
        else:
            dummy1cnt0 = c0
            dummy1cnt1 = c1 + 1

        logbetanew0 = logbetatimespe0 - logpw0
        if logbetanew0 > settings.maxlogbeta:
            logbetanew0 = settings.maxlogbeta
        if logbetanew0 < -settings.maxlogbeta:
            logbetanew0 = -settings.maxlogbeta

        logbetanew1 = logbetatimespe1 - logpw1
        if logbetanew1 > settings.maxlogbeta:
            logbetanew1 = settings.maxlogbeta
        if logbetanew1 < -settings.maxlogbeta:
            logbetanew1 = -settings.maxlogbeta

        dummy0info[curdepth] = (dummy0cnt0, dummy0cnt1, logbetanew0)
        dummy1info[curdepth] = (dummy1cnt0, dummy1cnt1, logbetanew1)

    if loggamma >= 0:
        ctwprob.logpwroot = -CTWjac(-loggamma)
        ctwprob.predsymb = 0
    else:
        ctwprob.logpwroot = -CTWjac(loggamma)
        ctwprob.predsymb = 1


ARENTRIES = 4096
ACCURACY_CTW = 128
STEPHALF = ARENTRIES


def ctw_steps(ctwprob: CTWProb) -> tuple[int, bool]:
    """Calculate stepsize from CTW probability.

    Args:
        ctwprob: CTW probability structure.

    Returns:
        (instep, symbsmall): stepsize and symbol with smallest probability.
    """
    instep = -ctwprob.logpwroot * (ARENTRIES // ACCURACY_CTW)
    symbsmall = 1 - ctwprob.predsymb

    if instep < 3:
        instep = 3

    return instep, bool(symbsmall)
