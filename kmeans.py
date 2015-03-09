import numpy as np
import random
import math
import logging

logging.getLogger(__name__).setLevel(logging.DEBUG)

# https://datasciencelab.wordpress.com/2013/12/12/clustering-with-k-means-in-python/

def cluster_points(X, mu):
    clusters  = {i:[] for i in range(len(mu))}
    for x in X:
        bestmukey = cluster_idx(x, mu)
        clusters[bestmukey].append(x)
        # clusters.setdefault(bestmukey, []).append(x)
    return clusters

def cluster_idx(x, mu):
    bestmu, key = min([(distance(x, mu_), i)
                      for i, mu_ in enumerate(mu)])
    return key

def distance(v1, v2):
    differences = sum([(p2-p1)**2 for (p1, p2) in zip(v1, v2)])
    return math.sqrt(differences)

def mean(x):
    return sum(x)/len(x)

def reevaluate_centers(mu, clusters):
    newmu = []
    keys = sorted(clusters.keys())
    for k in keys:
        newmu.append(np.mean(clusters[k], axis = 0))
    return newmu

def has_converged(mu, oldmu):
    return set([tuple(a) for a in mu]) == set([tuple(a) for a in oldmu])

def find_centers(X, K, trieslimit=10):
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

