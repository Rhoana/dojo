#!/usr/bin/env python

from _dojo.scripts.np2imgo import Imgo
from _dojo.scripts.np2sego import Sego
import matplotlib.pyplot as plt
import numpy as np
import glob
import cv2
import re
import os

in_folder = '../../../derp'
out_folder = '../../../out'
img_path = '/em_padded'
seg_path = '/np'
type = '/*.png'

blockshape = [2048,2048,40]
nothing = np.uint8(0)
shown = False
space = '_'
bit = 256

def hash(p):
    nums = [int(n) for n in p.split(space) if unicode(n).isnumeric()]
    if len(nums) == 4:
        nums = (nums[1:3]+nums[:1])*np.array(blockshape) + [0,0,nums[-1]]
    elif len(nums) == 3:
        nums = nums[1:3]+nums[:1]
    return nums

def grid(places):
    plt.axes()
    for row in places: plt.gca().add_patch(plt.Rectangle(row[1::-1], 1, 1, fc='k'))
    ax = plt.axis('scaled')
    plt.axis(ax[:2]+ax[:-3:-1])
    plt.show()


def convert(in_folder, out_folder):

    places = []
    folders = []
    ids = np.zeros([bit]*3,dtype=np.uint8)
    new_id = np.uint8(nothing+2)

    ## Z__Y__X to Y__X__Z
    for dirt in os.listdir(in_folder):
        dirt_path = os.path.join(in_folder, dirt)
        if os.path.isdir(dirt_path):
            places.append(hash(dirt))
            folders.append(dirt_path)
    places = np.array(places)
    if shown: grid(places)

    ## Make emtpty arrays
    layout = np.amax(places,0)+1
    all_shape = layout*blockshape
    img,seg = [np.zeros(all_shape)]*2
    edge = blockshape[:-1] + [1,]

    ## Fill arrays
    for fold in folders:
        seg_dirt = glob.glob(fold + seg_path)
        img_dirt = glob.glob(fold + img_path)
        if not seg_dirt: return 'segs not found'
        if not img_dirt: return 'imgs not found'


        ## Use each file in both subfolders of all folders
        for image in glob.glob(img_dirt[0] + type):
            spot = hash(os.path.basename(image))
            print  os.path.basename(image)
            print  spot
            print  '\n'
            if len(spot) != 3 or (np.clip(spot,0,all_shape-edge)-spot).any(): return 'imgs not in bounds'
            seg[spot[0]:(spot + edge)[0],spot[1]:(spot + edge)[1],spot[2]] = cv2.imread(image,0).T

        ## Use each file in both subfolders of all folderss
        for segment in glob.glob(seg_dirt[0] + type):
            spot = hash(os.path.basename(segment))
            print  os.path.basename(segment)
            print  spot
            print  '\n'
            if len(spot) != 3 or (np.clip(spot,0,all_shape-edge)-spot).any(): return 'segs not in bounds'
            # Read the image
            out_seg = []
            raw_seg = cv2.imread(segment).reshape(-1,3)
            if not raw_seg.any():
                result = np.ones(blockshape[:-1])
            else:
                for pix in raw_seg:
                    out_seg.append(ids[tuple(pix)])
                    if out_seg[-1] == np.uint8(0):
                        ids[tuple(pix)] = new_id
                        out_seg[-1] = new_id
                        new_id += 1
                result = np.array(out_seg).reshape(blockshape[:-1])

            ## Fill in the image
            img[spot[0]:(spot + edge)[0],spot[1]:(spot + edge)[1],spot[2]] = result



    # Do labels
    Sego(seg[:,:,2:], out_folder)

    # Do image
    Imgo(img[:,:,2:], out_folder)


err = convert(in_folder, out_folder)
if err: print 'err '+str(err)