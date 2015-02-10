import os
import os.path
import math
import random
import sys
from functools import partial

from PIL import Image
import numpy as np

import kmeans
from progress import progress

exts = ('jpg', 'png')
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
    dists = [(distance(pix, coord), coord) for coord in coords]
    closest = min(dists)
    return closest[1]

def makehist(fname):
    maxsize = (128, 128)

    im = Image.open(fname, 'r')
    im.thumbnail(maxsize) # modifies in place

    hist = np.array([0] * len(colors_p))

    for pix in im.getdata():
        color = closest(pix, colors_p)
        idx = colors_p.index(color)
        hist[idx] += 1

    npixels = im.size[0] * im.size[1]

    hist = np.array([float(x)/npixels for x in hist])

    # divide by the size
    #hist /= float(npixels)

    return hist

def main(filesdir, outdir, nclusters=10):
    hists = []

    fnames = os.listdir(filesdir)
    random.shuffle(fnames)
    #fnames = random.sample(fnames, 10)

    maps = {}

    for fname in progress(fnames, verbosity=1):
        if fname.startswith('.'):
            continue

        if not any(fname.lower().endswith(x) for x in exts):
            continue

        fname = os.path.join(filesdir, fname)
        hist = makehist(fname)
        maps[id(hist)] = fname
        hists.append(hist)

    mu, clusters = kmeans.find_centers(hists, nclusters)

    for num, cluster in clusters.iteritems():
        mymu = mu[num]
        os.makedirs(os.path.join(outdir, str(num)))
        cluster.sort(key=partial(distance, mymu))
        for i, item in enumerate(cluster):
            fname = maps[id(item)]
            toname = os.path.join(outdir, str(num), '%03d.jpg' % (i,))
            print 'link', fname, toname
            os.link(fname, toname)

indir, outdir = sys.argv[1:]
main(indir, outdir)

