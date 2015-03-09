#!/usr/bin/env python

import sqlite3
import itertools
import argparse
import os
import os.path
import math
import random
import sys
from functools import partial
import colorsys
import logging
from multiprocessing import Pool, cpu_count
import pickle

from PIL import Image
#import numpy as np

import kmeans
from progress import progress

exts = ('jpg', 'png', 'pef')

logging.getLogger(__name__).setLevel(logging.DEBUG)

def make_colors():
    # TODO these are very probably terrible initial values

    values = map(float, [0, 255/4*1, 255/4*2, 255/4*3, 255])
    colors = []
    for x in values:
        for y in values:
            for z in values:
                colors.append((x,y,z))
    colors.sort()
    return colors

colors_p = make_colors()


def makehist(fname):
    maxsize = (128, 128)

    im = Image.open(fname, 'r')

    # the resizing operation in C is faster than the counting operation in Python,
    # so this makes us much faster while losing very little data
    im.thumbnail(maxsize) # modifies in place

    # get it into RGB first if it's not (e.g. pallet-based images)
    im = im.convert('RGB')
    npixels = im.size[0] * im.size[1]

    # this turns out to be similar to the gathering phase of a
    # kmeans operation so just reuse that
    pixxs = kmeans.cluster_points(im.getdata(), colors_p)
    hist = [len(y)/float(npixels) for (x,y) in sorted(pixxs.items())]

    return fname, hist

def printer(x):
    try:
        return x[:50].encode('utf8')
    except UnicodeDecodeError:
        return 'unprintable'

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('--cache', dest='cache', default=None)
    parser.add_argument('-n', dest='num_clusters', type=int, default=10)
    parser.add_argument('-j', dest='concurrency', type=int,
                        default=cpu_count())

    parser.add_argument('indir')
    parser.add_argument('outdir')

    args = parser.parse_args()

    if args.indir == '-':
        fnames = map(lambda s: s.rstrip('\n'), sys.stdin)
    else:
        fnames = os.listdir(args.indir)
        fnames = [os.path.join(args.indir, fn)
                  for fn in fnames
                  if not fn.startswith('.')
                  and any(fn.lower().endswith(x) for x in exts)]

    hists = {}

    # after clustering, we just get the clustered coordinates back. this lets
    # us map them back to the source fnames instead of coordinates
    maps = {}

    # the cache connection if we have one
    conn = None

    if args.cache:
        conn = sqlite3.connect(args.cache)
        conn.text_factory = str

        conn.execute("""
                     CREATE TABLE IF NOT EXISTS histcache(fname PRIMARY KEY, hist)
                     """)

        # clean up the cache by deleting any entries that aren't present in the
        # dataset
        conn.execute('CREATE TEMPORARY TABLE wantfiles(fname)')
        for fname in fnames:
            conn.execute("INSERT INTO wantfiles(fname) VALUES(?)",
                         (fname,))

        curs = conn.cursor()

        curs.execute("""
                     DELETE FROM histcache
                     WHERE fname NOT IN (SELECT fname FROM wantfiles)
                     """)
        if curs.rowcount:
            logging.debug("Deleted %d stale entries from the histcache",
                          curs.rowcount)

        cachedhists = list(conn.execute('SELECT fname, hist FROM histcache'))

        for fname, hist in cachedhists:
            hist = pickle.loads(hist)
            hists[fname] = hist
            maps[id(hist)] = fname

    searchfnames = [ fname for fname in fnames if fname not in hists ]

    if searchfnames:
        # this just makes the progress bar more accurate
        random.shuffle(searchfnames)

        pool = Pool(processes=args.concurrency)

        #results = itertools.imap(makehist, searchfnames)
        results = pool.imap_unordered(makehist, searchfnames, chunksize=1)

        for fname, hist in progress(results,
                                    verbosity=1,
                                    estimate=len(searchfnames),
                                    key=lambda x: printer(x[0])):
            maps[id(hist)] = fname
            hists[fname] = hist

            if conn:
                aspickle = pickle.dumps(hist)
                conn.execute("INSERT INTO histcache(fname, hist) VALUES(?, ?)",
                             (fname, aspickle))
                conn.commit()

    mu, clusters = kmeans.find_centers(hists.values(), args.num_clusters)

    for num, cluster in clusters.iteritems():
        mymu = mu[num]
        bdir = os.path.join(args.outdir, '%02d' % (num,))
        os.makedirs(bdir)
        cluster = [ (kmeans.distance(mymu, x), x)
                    for x in cluster ]
        cluster.sort()
        for i, (distance, item) in enumerate(cluster):
            fname = maps[id(item)]
            toname = os.path.join(bdir, '%03d_%.8f.jpg' % (i, distance))
            os.link(fname, toname)

main(sys.argv)

