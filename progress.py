import sys
import itertools
from datetime import datetime

def timedelta_to_seconds(td):
    return td.days * (24*60*60) + td.seconds + (float(td.microseconds) / 1000000)


def format_timedelta(td, sep='', sigunits=2):
    s = timedelta_to_seconds(td)
    return format_seconds(s, sep = sep, sigunits = sigunits)


def format_seconds(s, sep='', sigunits=2):
    ret = []
    if s < 0:
        neg = True
        s *= -1
    else:
        neg = False

    if s >= (24 * 60 * 60):
        days = int(s // (24 * 60 * 60))
        ret.append('%dd' % days)
        s -= days * (24 * 60 * 60)
    if s >= 60 * 60:
        hours = int(s // (60 * 60))
        ret.append('%dh' % hours)
        s -= hours * (60 * 60)
    if s >= 60:
        minutes = int(s // 60)
        ret.append('%dm' % minutes)
        s -= minutes * 60
    if s >= 1:
        seconds = int(s)
        ret.append('%ds' % seconds)
        s -= seconds

    if not ret:
        return '0s'

    if sigunits is None:
        outp = sep.join(ret)
    else:
        # if it's going to be more than 2d6h, the fact that it's really
        # 2d6h2m38s may not actually that much more information, so let them
        # say how many output units matter.
        outp = sep.join(ret[:sigunits])

    return ('-' if neg else '') + outp

def guess_time_remaining(total_work, work_so_far, start_time):
    """
    Try to figure out how much longer some job will take given the total_work
    and work_so_far. Return a string like "5h2m"
    """

    # don't let this fold to zero
    elapsed = (time_m.time() - start_time) or 0.001
    rate = float(work_so_far)/elapsed
    remaining = total_work - work_so_far
    etr = format_seconds(int(float(remaining) / rate)) if rate else '(unknown)'

    return etr


def progress(it, verbosity=100, key=repr, estimate=None, persec=True,
             summary=True, itemtitle='items', termmagic=True, fd=sys.stderr):
    """An iterator that yields everything from `it', but prints progress
       information along the way, including time-estimates if
       possible"""

    # number of characters on the previous line we printed (required for
    # cleaning it before we print the next one
    prevline = 0

    now = start = datetime.now()
    elapsed = start - start

    # try to guess at the estimate if we can
    if estimate is None:
        try:
            estimate = len(it)
        except TypeError:
            pass

    def format_datetime(dt, show_date=False, show_seconds=True):
        if show_date:
            return dt.strftime('%Y-%m-%d %H:%M')
        elif show_seconds:
            return dt.strftime('%H:%M:%S')
        else:
            return dt.strftime('%H:%M')

    def deq(dt1, dt2):
        "Indicates whether the two datetimes' dates describe the same (day,month,year)"
        d1, d2 = dt1.date(), dt2.date()
        return (    d1.day   == d2.day
                and d1.month == d2.month
                and d1.year  == d2.year)

    if estimate:
        fd.write('Starting at %s to process %d %s\n'
                 % (format_datetime(start,True), estimate, itemtitle))
    else:
        fd.write('Starting at %s to process %s\n'
                 % (format_datetime(start,True), itemtitle))

    # we're going to itertools.islice it so we need to start an iterator
    it = iter(it)

    seen = 0
    while True:
        this_chunk = 0
        thischunk_started = datetime.now()

        # the simple bit: just iterate and yield
        for item in itertools.islice(it, verbosity):
            this_chunk += 1
            seen += 1
            yield item

        if this_chunk < verbosity:
            # we're done, the iterator is empty
            break

        now = datetime.now()
        elapsed = now - start
        thischunk_seconds = timedelta_to_seconds(now - thischunk_started)

        if estimate:
            # the estimate is based on the total number of items that we've
            # processed in the total amount of time that's passed, so it should
            # smooth over momentary spikes in speed (but will take a while to
            # adjust to long-term changes in speed)
            remaining = ((elapsed/seen)*estimate)-elapsed
            completion = now + remaining
            count_str = ('%d/%d %.2f%%'
                         % (seen, estimate, float(seen)/estimate*100))
            completion_str = format_datetime(completion,
                                             # only show the date if it's not today
                                             not deq(completion,now),
                                             # only show the seconds if they matter
                                             timedelta_to_seconds(remaining) < 5*60)
            estimate_str = (' (%s remaining; completion %s)'
                            % (format_timedelta(remaining),
                               completion_str))
        else:
            count_str = '%d' % seen
            estimate_str = ''

        if key:
            key_str = ': %s' % key(item)
        else:
            key_str = ''

        # unlike the estimate, the persec count is the number per second for
        # *this* batch only, without smoothing
        if persec and thischunk_seconds > 0:
            persec_str = ' (%.1f/s)' % (float(this_chunk)/thischunk_seconds,)
        else:
            persec_str = ''

        toprint = ('%s%s, %s%s%s'
                   % (count_str, persec_str,
                      format_timedelta(elapsed), estimate_str, key_str))
        if termmagic:
            if prevline > len(toprint):
                # clear the previous line
                fd.write('\r%s' % (' '*prevline))
            prevline = len(toprint)
            fd.write('\r%s' % toprint.encode('utf8'))
        else:
            fd.write('%s\n' % toprint.encode('utf8'))
        fd.flush() # combat line-buffering

    now = datetime.now()
    elapsed = now - start
    elapsed_seconds = timedelta_to_seconds(elapsed)
    if persec and seen > 0 and elapsed_seconds > 0:
        persec_str = ' (@%.1f/sec)' % (float(seen)/elapsed_seconds)
    else:
        persec_str = ''
    if termmagic:
        fd.write('\n')
    if summary:
        fd.write('Processed %d%s %s in %s..%s (%s)\n'
                 % (seen,
                    persec_str,
                    itemtitle,
                    format_datetime(start, not deq(start, now)),
                    format_datetime(now, not deq(start, now)),
                    format_timedelta(elapsed)))
    fd.flush()
