#!/usr/bin/env python

from np2imgo import Imgo
from np2sego import Sego
import numpy as np
import shutil
import glob
import cv2
import sys
import os

class convert:
    def __init__(self, _here, _infold, _outfold,_ipath,_spath,_ty,_sp):

        slices = []
        b_ = (1,256,65536)
        here = os.path.dirname(_here)
        _infold,_outfold = [os.path.normpath(os.path.join(here,pa)) for pa in [_infold,_outfold]]

        s_file = glob.glob(os.path.join(_infold, _spath))[0]
        i_file = glob.glob(os.path.join(_infold, _ipath))[0]
        all_shape = [2048,2048,300]

        # clear directories
        if os.path.exists(_outfold): shutil.rmtree(_outfold)
        else : print 'making ', _outfold
        os.mkdir(_outfold)
        self._sp = _sp

        # Do labels
        segger = Sego(_outfold)
        # Do image
        imgger = Imgo(_outfold)

        for segment in glob.glob(os.path.join(s_file,_ty)):
            spot = self.hash(os.path.splitext(os.path.basename(segment))[0])

            segger.run(np.dot(cv2.imread(segment),b_),spot)

        for image in glob.glob(os.path.join(i_file,_ty)):
            spot = self.hash(os.path.splitext(os.path.basename(image))[0])
            imgger.run(cv2.imread(image,0),spot)

        segger.save(all_shape)
        imgger.save(all_shape)

    def err(self,e):
        sys.stderr.write(e)
        quit()


    def hash(self,p):
        return int(p[-3:])

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