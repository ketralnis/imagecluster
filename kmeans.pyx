import numpy as np
import random
import math
import logging

cdef extern from "math.h":
    double sqrt(double x)

logging.getLogger(__name__).setLevel(logging.DEBUG)

# https://datasciencelab.wordpress.com/2013/12/12/clustering-with-k-means-in-python/

cpdef dict cluster_points(X, list mu):
    cdef dict clusters = {i:[] for i in range(len(mu))}
    cdef tuple x
    cdef list inter
    cdef int bestmukey

    for x in X:
        bestmukey = cluster_idx(x, mu)
        inter = clusters[bestmukey]
        inter.append(x)

    return clusters


cpdef int cluster_idx(tuple x, list mu):
    # given a point x and a list of centres mu, return the
    # index of the centre that minimises the distance to x
    cdef int i
    cdef tuple mu_
    cdef int key = -1
    cdef float bestdistance = -1
    for i, mu_ in enumerate(mu):
        thisdistance = distance(x, mu_)
        if bestdistance == -1 or bestdistance > thisdistance:
            bestdistance = thisdistance
            key = i
    return key


cpdef float distance(tuple v1, tuple v2):
    cdef float sumofsquares = 0.0
    cdef float p1
    cdef float p2
    cdef float square

    for x in range(len(v1)):
        p1 = v1[x]
        p2 = v2[x]
        diff = p2-p1
        square = diff**2
        sumofsquares += square

    return sqrt(sumofsquares)


cpdef list reevaluate_centers(dict clusters):
    cdef list newmu = []
    cdef list keys = sorted(clusters.keys())
    cdef int k
    for k in keys:
        newmu.append(tuple(np.mean(clusters[k], axis = 0)))
    return newmu


cpdef has_converged(list mu, list oldmu):
    return set([tuple(a) for a in mu]) == set([tuple(a) for a in oldmu])


cpdef tuple find_centers(list X, int K, int trieslimit=10):
    # Initialize to K random centers
    cdef list oldmu = random.sample(X, K)
    cdef list mu = random.sample(X, K)

    cdef int tries = 0

    while not has_converged(mu, oldmu):
        tries += 1
        if trieslimit and tries >= trieslimit:
            logging.debug("Quitting after %d tries", tries)
            break
        oldmu = mu
        # Assign all points in X to clusters
        clusters = cluster_points(X, mu)
        logging.info("Clustering Attempt #%d: %r", tries, map(len, clusters.itervalues()))
        # Reevaluate centers
        mu = reevaluate_centers(clusters)

    return mu, clusters

