import numpy as np
import random
import math
import logging

cdef extern from "math.h":
    double sqrt(double x)

logging.getLogger(__name__).setLevel(logging.DEBUG)

# https://datasciencelab.wordpress.com/2013/12/12/clustering-with-k-means-in-python/

cpdef dict cluster_points(list X, list mu):
    cdef dict clusters = {i:[] for i in range(len(mu))}
    cdef tuple x
    cdef int bestmukey

    for x in X:
        bestmukey = cluster_idx(x, mu)
        clusters[bestmukey].append(x)
    return clusters

cpdef int cluster_idx(tuple x, list mu):
    cdef int i
    cdef tuple mu_
    bestmu, key = min([(distance(x, mu_), i)
                      for i, mu_ in enumerate(mu)])
    return key


cpdef float distance(tuple v1, tuple v2):
    cdef float sumofsquares = 0.0
    cdef float p1
    cdef float p2
    cdef float square

    #differences = sum([(p2-p1)**2 for (p1, p2) in zip(v1, v2)])
    #return math.sqrt(differences)

    for x in range(len(v1)):
        p1 = v1[x]
        p2 = v2[x]
        diff = p2-p1
        square = diff**2
        sumofsquares += square

    return sqrt(sumofsquares)

cpdef list reevaluate_centers(list mu, dict clusters):
    cdef list newmu = []
    cdef int keys = sorted(clusters.keys())
    for k in keys:
        newmu.append(tuple(np.mean(clusters[k], axis = 0)))
    return newmu

cpdef has_converged(list mu, list oldmu):
    cdef list a
    return set([tuple(a) for a in mu]) == set([tuple(a) for a in oldmu])

cpdef tuple find_centers(X, K, trieslimit=10):
    # Initialize to K random centers
    oldmu = random.sample(X, K)
    mu = random.sample(X, K)
    tries = 0
    while not has_converged(mu, oldmu):
        tries += 1
        if trieslimit and tries >= trieslimit:
            break
        oldmu = mu
        # Assign all points in X to clusters
        clusters = cluster_points(X, mu)
        logging.info("Clustering Attempt #%d: %r", tries, map(len, clusters.itervalues()))
        # Reevaluate centers
        mu = reevaluate_centers(oldmu, clusters)

    return mu, clusters

