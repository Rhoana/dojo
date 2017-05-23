#!/usr/bin/env python

from _dojo.scripts.np2imgo import Imgo
from _dojo.scripts.np2sego import Sego
from os import getcwd
import glob
import h5py
import re

in_folder = '../../../in'
out_folder = '../../../out'

find = lambda r,x: (x[i] for i in range(len(x)) if re.search(r,x[i]))

def convert(in_folder, out_folder):
    files = glob.glob( in_folder + '/*.h5')
    if not files : return 'no h5 found'
    for fil in files:
        f = h5py.File(fil, 'r')

        # if labels in file
        groups = f.keys()
        seg = next(find(r'label',groups),-1)
        if seg < 0 : return 'no labels found'
        shape = f[seg].shape
        groups.remove(seg)

        # if image has same size
        images = list(find(r'image',groups))
        if not images: return 'no images found'
        img = next((i for i in images if f[i].shape == shape),-1)
        if img < 0: return 'label shape not same as image shape'

        # Do labels
        Sego(f[seg], out_folder)

        # Do image
        Imgo(f[img], out_folder)

        f.close()

err = convert(in_folder, out_folder)
if err: print 'err '+str(err)