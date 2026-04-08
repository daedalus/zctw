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
from zctw.ctwtree import CTWRecord
from zctw.settings import CTWSettings


class CTWProb:
    """CTW probability information."""

    __slots__ = ("logpwroot", "predsymb")

    def __init__(self, logpwroot: int = 0, predsymb: int = 0):
        self.logpwroot = logpwroot
        self.predsymb = predsymb


def ctw_data_from_one_count(bit: int) -> CTWRecord:
    """Create CTWRecord with one count."""
    temp = CTWRecord()
    temp.cnt[bit] = 1
    temp.cnt[1 - bit] = 0
    temp.logbeta = 0
    return temp


def ctw_process(
    curdepth: int,
    ctwinfo: list[CTWRecord],
    ctwprob: CTWProb,
    dummy0info: list[CTWRecord],
    dummy1info: list[CTWRecord],
    settings: CTWSettings,
) -> None:
    """Process CTW tree to get weighted probability.

    Args:
        curdepth: Current depth in tree.
        ctwinfo: CTW info for each node on path.
        ctwprob: Output probability structure.
        dummy0info: Output for dummy 0 update.
        dummy1info: Output for dummy 1 update.
        settings: CTW settings.
    """
    # Start with deepest node
    curdepth -= 1
    data = ctwinfo[curdepth]
    c0 = data.cnt[0]
    c1 = data.cnt[1]

    # Calculate loggamma using zero-redundancy or KT estimator
    if settings.use_zeroredundancy and (c1 == 0 or c0 == 0):
        if c1 == 0:
            loggamma = CTWzlogpmax[c0] - CTWzlogpmin[c0]
        else:
            loggamma = CTWzlogpmin[c1] - CTWzlogpmax[c1]
    else:
        loggamma = CTWlogar[2 * c0 + 1] - CTWlogar[2 * c1 + 1]

    # Update counts for dummy0 and dummy1
    if c0 == (MAXCOUNTS - 1):
        dummy0info[curdepth].cnt[0] = MAXCOUNTS // 2
        dummy0info[curdepth].cnt[1] = (c1 + 1) // 2
    else:
        dummy0info[curdepth].cnt[0] = c0 + 1
        dummy0info[curdepth].cnt[1] = c1

    if c1 == (MAXCOUNTS - 1):
        dummy1info[curdepth].cnt[0] = (c0 + 1) // 2
        dummy1info[curdepth].cnt[1] = MAXCOUNTS // 2
    else:
        dummy1info[curdepth].cnt[0] = c0
        dummy1info[curdepth].cnt[1] = c1 + 1

    dummy0info[curdepth].logbeta = data.logbeta
    dummy1info[curdepth].logbeta = data.logbeta

    # Determine end depth based on root weighting
    if settings.rootweighting:
        enddepth = 0
    else:
        enddepth = 1

    # Process remaining nodes
    while curdepth > enddepth:
        curdepth -= 1
        data = ctwinfo[curdepth]

        # Calculate incoming weighted probabilities
        if loggamma >= 0:
            logpw0 = -CTWjac(-loggamma)
            logpw1 = logpw0 - loggamma
        else:
            logpw1 = -CTWjac(loggamma)
            logpw0 = logpw1 + loggamma

        # Calculate conditional estimated probabilities
        c0 = data.cnt[0]
        c1 = data.cnt[1]

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

        # Calculate new loggamma
        logbetatimespe0 = data.logbeta + logpe0
        diff0 = logbetatimespe0 - logpw0
        if diff0 >= 0:
            nom = logbetatimespe0 + CTWjac(-diff0)
        else:
            nom = logpw0 + CTWjac(diff0)

        logbetatimespe1 = data.logbeta + logpe1
        diff1 = logbetatimespe1 - logpw1
        if diff1 >= 0:
            den = logbetatimespe1 + CTWjac(-diff1)
        else:
            den = logpw1 + CTWjac(diff1)

        loggamma = nom - den

        # Update counts for dummy0 and dummy1
        if c0 == (MAXCOUNTS - 1):
            dummy0info[curdepth].cnt[0] = MAXCOUNTS // 2
            dummy0info[curdepth].cnt[1] = (c1 + 1) // 2
        else:
            dummy0info[curdepth].cnt[0] = c0 + 1
            dummy0info[curdepth].cnt[1] = c1

        if c1 == (MAXCOUNTS - 1):
            dummy1info[curdepth].cnt[0] = (c0 + 1) // 2
            dummy1info[curdepth].cnt[1] = MAXCOUNTS // 2
        else:
            dummy1info[curdepth].cnt[0] = c0
            dummy1info[curdepth].cnt[1] = c1 + 1

        # Calculate logbeta for dummy updates
        logbetanew0 = logbetatimespe0 - logpw0
        if logbetanew0 > settings.maxlogbeta:
            logbetanew0 = settings.maxlogbeta
        if logbetanew0 < -settings.maxlogbeta:
            logbetanew0 = -settings.maxlogbeta
        dummy0info[curdepth].logbeta = logbetanew0

        logbetanew1 = logbetatimespe1 - logpw1
        if logbetanew1 > settings.maxlogbeta:
            logbetanew1 = settings.maxlogbeta
        if logbetanew1 < -settings.maxlogbeta:
            logbetanew1 = -settings.maxlogbeta
        dummy1info[curdepth].logbeta = logbetanew1

    # Put weighted probability and most probable symbol in ctwprob
    if loggamma >= 0:
        ctwprob.logpwroot = -CTWjac(-loggamma)
        ctwprob.predsymb = 0
    else:
        ctwprob.logpwroot = -CTWjac(loggamma)
        ctwprob.predsymb = 1


# Constant from larc module
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
    # Calculate stepsize from logpwroot
    instep = -ctwprob.logpwroot * (ARENTRIES // ACCURACY_CTW)

    # Least probable symbol
    symbsmall = 1 - ctwprob.predsymb

    # Minimum stepsize is 3
    if instep < 3:
        instep = 3

    return instep, bool(symbsmall)
