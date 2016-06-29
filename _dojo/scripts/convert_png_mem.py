#!/usr/bin/env python

from np2imgo import Imgo
from np2sego import Sego
import numpy as np
import shutil
import h5py
import time
import glob
import cv2
import sys
import os

class convert:
    def __init__(self, _here, _infold, _outfold,_ipath,_sepath,_ty,_sp,_skip):

        places = []
        folders = []
        b_ = (1,256,65536)
        here = os.path.dirname(_here)
        _infold,_outfold = [os.path.normpath(os.path.join(here,pa)) for pa in [_infold,_outfold]]

        a_fold = ( d for d in os.listdir(_infold) if os.path.isdir(os.path.join(_infold, d)) ).next()
        a_file = glob.glob(os.path.join(os.path.join(_infold, a_fold), _ipath))
        if not a_file: self.err('no folder matching '+ _ipath + ' in /'+ a_fold + '\n')
        a_box = glob.glob(os.path.join(a_file[0],_ty))
        if not a_box: self.err('no'+_ty+'in /'+ a_file +'\n')
        a_pic = cv2.imread(a_box[0],0)
        # glob.glob(os.path.join(img_dirt[0],_ty)

        self._skip = _skip
        self._slice = list(a_pic.shape) + [1,]
        self._box = list(a_pic.shape) + [len(a_box)-_skip,]
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
        all_z = all_shape[-1]
        print 'there are ', layout, ' slices'
        print 'each slice is ', self._slice, ' pixels'
        print 'there are ', all_shape, ' pixels\n'

        # clear directories
        if os.path.exists(_outfold): shutil.rmtree(_outfold)
        else : print 'making ', _outfold
        os.mkdir(_outfold)


        # Do labels
        segger = Sego(_outfold)
        # Do image
        imgger = Imgo(_outfold)

        for now_z in range(self._skip,all_z):

            img = np.zeros(all_shape[:-1],dtype=np.uint8)
            seg = np.zeros(all_shape[:-1],dtype=np.uint32)

            ## Fill arrays
            for fold in folders:
                seg_dirt = glob.glob(os.path.join(fold, _sepath))
                img_dirt = glob.glob(os.path.join(fold, _ipath))
                if not seg_dirt: self.err('segs not found')
                if not img_dirt: self.err('imgs not found')

                ## Use each file in both subfolders of all folders
                for image in glob.glob(os.path.join(img_dirt[0],_ty)):
                    spot = self.hash(os.path.basename(image))
                    if spot[2] != now_z: continue

                    if len(spot) != 3 or (np.clip(spot,0,all_shape)-spot).any(): self.err('imgs not in bounds')
                    img[spot[0]:(spot + self._slice)[0],spot[1]:(spot + self._slice)[1]] = cv2.imread(image,0)

                #     print  os.path.basename(image)
                #     print  spot
                # print  '\n'

                ## Use each file in both subfolders of all folderss
                for segment in glob.glob(os.path.join(seg_dirt[0],_ty)):
                    spot = self.hash(os.path.basename(segment))
                    if spot[2] != now_z: continue

                    if len(spot) != 3 or (np.clip(spot,0,all_shape)-spot).any(): self.err('segs not in bounds')
                    seg[spot[0]:(spot + self._slice)[0],spot[1]:(spot + self._slice)[1]] = np.dot(cv2.imread(segment),b_)

                #     print  os.path.basename(segment)
                #     print  spot
                # print  '\n'

            segger.run(seg,now_z-self._skip)
            imgger.run(img,now_z-self._skip)

            print 'done w/ z=', now_z-self._skip

        segger.save(all_shape)
        imgger.save(all_shape)


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
    lost = 1

    args = [here,in_folder, out_folder,img_path,seg_path,type,space,lost]
    for si,sa in enumerate(sys.argv): args[si] = sa

    convert(*args)