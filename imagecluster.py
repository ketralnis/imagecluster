import os
import os.path
import math
import random
import sys
from functools import partial
import colorsys
import logging

from PIL import Image
import numpy as np
import pipeline

import kmeans
from progress import progress

exts = ('jpg', 'png', 'pef')
#colors = {
#    'black': (0, 0, 0),
#    'red': (255, 0, 0),
#    'redgreen': (255, 255, 0),
#    'green': (0, 255, 0),
#    'greenblue': (0, 255, 255),
#    'blue': (0, 0, 255),
#    'redblue': (255, 0, 255),
#    'white': (255, 255, 255),
#}
values = [0, 255/2, 255]
colors_p = []
for x in values:
    for y in values:
        for z in values:
            colors_p.append((x,y,z))
colors_p.sort()

def distance(v1, v2):
    diffs = [(p2-p1)**2 for (p1, p2) in zip(v1, v2)]
    return math.sqrt(sum(diffs))


def closest(pix, coords):
    dists = [(distance(pix, coord), i) for i, coord in enumerate(coords)]
    dist, which = min(dists)
    return which


def getimage(fname):
    maxsize = (128, 128)

    im = Image.open(fname, 'r')
    im.thumbnail(maxsize) # modifies in place
    im = im.convert('RGB')
    return im


def makehist(im):
    hist = np.array([0] * len(colors_p))

    for pix in im.getdata():
        try:
            pix = colorsys.rgb_to_hsv(*pix)
        except Exception:
            logging.exception("wtf? %r", pix)
        idx = closest(pix, colors_p)
        hist[idx] += 1

    npixels = im.size[0] * im.size[1]

    hist = np.array([float(x)/npixels for x in hist])

    # divide by the size
    #hist /= float(npixels)

    return hist


def main(filesdir, outdir, nclusters=5):
    hists = []

    fnames = os.listdir(filesdir)
    fnames = [os.path.join(filesdir, fn)
              for fn in fnames
              if not fn.startswith('.')
              and any(fn.lower().endswith(x) for x in exts)]
    random.shuffle(fnames)
    #fnames = random.sample(fnames, 10)

    pl = pipeline.Pipeline([
        pipeline.Generator(fnames),
        pipeline.MultiMapper(lambda fname: (fname, getimage(fname)), 2),
        pipeline.Mapper(lambda tup: (tup[0], makehist(tup[1]))),
    ], bufsize=5)

    maps = {}

    for fname, hist in progress(pl, verbosity=1, estimate=len(fnames),
                                key=lambda x: x[0]):
        maps[id(hist)] = fname
        hists.append(hist)

    mu, clusters = kmeans.find_centers(hists, nclusters)

    for num, cluster in clusters.iteritems():
        mymu = mu[num]
        bdir = os.path.join(outdir, '%02d' % (num,))
        os.makedirs(bdir)
        cluster.sort(key=partial(distance, mymu))
        for i, item in enumerate(cluster):
            fname = maps[id(item)]
            toname = os.path.join(bdir, '%03d.jpg' % (i,))
            print 'link', fname, toname
            os.link(fname, toname)

indir, outdir = sys.argv[1:]
main(indir, outdir)

