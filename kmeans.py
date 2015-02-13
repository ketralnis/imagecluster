import numpy as np
import random

# https://datasciencelab.wordpress.com/2013/12/12/clustering-with-k-means-in-python/
 
def cluster_points(X, mu):
    clusters  = {}
    for x in X:
        bestmukey = cluster_idx(x, mu)
        try:
            clusters[bestmukey].append(x)
        except KeyError:
            clusters[bestmukey] = [x]
    return clusters

def cluster_idx(x, mu):
    bestmukey = min([(np.linalg.norm(x-mu[i[0]]), i[0])
                     for i in enumerate(mu)])[1]
    return bestmukey

def reevaluate_centers(mu, clusters):
    newmu = []
    keys = sorted(clusters.keys())
    for k in keys:
        newmu.append(np.mean(clusters[k], axis = 0))
    return newmu
 
def has_converged(mu, oldmu):
    return set([tuple(a) for a in mu]) == set([tuple(a) for a in oldmu])
 
def find_centers(X, K):
    # Initialize to K random centers
    oldmu = random.sample(X, K)
    mu = random.sample(X, K)
    while not has_converged(mu, oldmu):
        oldmu = mu
        # Assign all points in X to clusters
        clusters = cluster_points(X, mu)
        # Reevaluate centers
        mu = reevaluate_centers(oldmu, clusters)
    return(mu, clusters)

