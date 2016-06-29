#!/usr/bin/env python

from np2imgo import Imgo
from np2sego import Sego
import numpy as np
import shutil
import time
import glob
import cv2
import sys
import os

class convert:
    def __init__(self, _here, _infold, _outfold,_ipath,_sepath,_ty,_sp):

        places = []
        folders = []
        b_ = (65536,256,1)
        here = os.path.dirname(_here)
        _infold,_outfold = [os.path.normpath(os.path.join(here,pa)) for pa in [_infold,_outfold]]

        a_fold = ( d for d in os.listdir(_infold) if os.path.isdir(os.path.join(_infold, d)) ).next()
        a_file = glob.glob(os.path.join(os.path.join(_infold, a_fold), _ipath))
        if not a_file: self.err('no folder matching '+ _ipath + ' in /'+ a_fold + '\n')
        a_box = glob.glob(os.path.join(a_file[0],_ty))
        if not a_box: self.err('no'+_ty+'in /'+ a_file +'\n')
        a_pic = cv2.imread(a_box[0],0)
        # glob.glob(os.path.join(img_dirt[0],_ty)

        self._box = list(a_pic.shape) + [len(a_box),]
        self._sp = _sp

        print '\nfrom ', _infold
        print 'to ', _outfold

        ## Z__Y__X to Y__X__Z
        for dirt in os.listdir(_infold):
            dirt_path = os.path.join(_infold, dirt)
            if os.path.isdir(dirt_path):
                places.append(self.hash(dirt))
                folders.append(dirt_path)

        ## Make emtpty arrays
        layout = np.amax(np.array(places),0)+1
        all_shape = layout*self._box
        print 'there are ', layout, ' boxes'
        print 'each box is ', self._box, ' voxels'
        print 'there are ', all_shape, ' voxels\n'
        img = np.zeros(all_shape)
        seg = np.zeros(all_shape)
        edge = self._box[:-1] + [1,]
        t0 = time.time()

        ## Fill arrays
        for fold in folders:
            seg_dirt = glob.glob(os.path.join(fold, _sepath))
            img_dirt = glob.glob(os.path.join(fold, _ipath))
            if not seg_dirt: self.err('segs not found')
            if not img_dirt: self.err('imgs not found')


            ## Use each file in both subfolders of all folders
            for image in glob.glob(os.path.join(img_dirt[0],_ty)):
                spot = self.hash(os.path.basename(image))

                if len(spot) != 3 or (np.clip(spot,0,all_shape-edge)-spot).any(): self.err('imgs not in bounds')
                img[spot[0]:(spot + edge)[0],spot[1]:(spot + edge)[1],spot[2]] = cv2.imread(image,0)

                print  os.path.basename(image)
                print  spot

            print  '\n'

            ## Use each file in both subfolders of all folderss
            for segment in glob.glob(os.path.join(seg_dirt[0],_ty)):
                spot = self.hash(os.path.basename(segment))

                if len(spot) != 3 or (np.clip(spot,0,all_shape-edge)-spot).any(): self.err('segs not in bounds')
                seg[spot[0]:(spot + edge)[0],spot[1]:(spot + edge)[1],spot[2]] = np.dot(cv2.imread(segment),b_)

                print  os.path.basename(segment)
                print  spot

            print  '\n'

        print 'done in ', time.time() - t0, ' secs'

        # clear directories
        if os.path.exists(out_folder): shutil.rmtree(out_folder)
        else : print 'making ', out_folder
        os.mkdir(out_folder)

        # Do labels
        Sego(seg[:,:,1:], _outfold)

        # Do image
        Imgo(img[:,:,1:], _outfold)

    def hash(self,p):
        nums = [int(n) for n in p.split(self._sp) if unicode(n).isnumeric()]
        if len(nums) == 4:
            nums = (nums[1:3]+nums[:1])*np.array(self._box) + [0,0,nums[-1]]
        elif len(nums) == 3:
            nums = nums[1:3]+nums[:1]
        return nums

    def err(self,e):
        sys.stderr.write(e)
        quit()

#
# entry point
#
if __name__ == "__main__":

    here = '~/convert_png.py'
    in_folder = '../../../in'
    out_folder = '../../../out'
    img_path = 'em*'
    seg_path = 'np'
    type = '*.png'
    space = '_'

    args = [here,in_folder, out_folder,img_path,seg_path,type,space]
    for si,sa in enumerate(sys.argv): args[si] = sa

    convert(*args)