#!/bin/sh

set -e

python ./setup.py build
export PYTHONPATH=$(pwd)/build/lib.macosx-10.4-x86_64-2.7

rm -fr /tmp/imagecluster
mkdir /tmp/imagecluster
find hotelimages -type f | time ./imagecluster.py --cache=tmp.cache -j4 -n20 - /tmp/imagecluster

open /tmp/imagecluster

