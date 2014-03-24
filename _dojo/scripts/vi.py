import partition_comparison as pc
import mahotas as mh
import tifffile as tif
import os
import numpy as np

segs = tif.imread('/home/d/TMP/DOJO/mojo_400_5_orig/cut-train-segs.tif')
gt = tif.imread('/home/d/TMP/DOJO/mojo_400_5_orig/cut-train-labels.tif')


print 'VI groundtruth vs. groundtruth:', pc.variation_of_information(gt.astype(np.uint32).ravel(), gt.astype(np.uint32).ravel())
print 'VI groundtruth vs. pipeline:',pc.variation_of_information(segs.ravel(), gt.astype(np.uint32).ravel())

proofreads = '/tmp/S1/'

out_is_there = False
out = None

out = np.zeros((10,1024,1024),dtype=np.uint32)

for k,i in enumerate(sorted(os.listdir(proofreads))):
  print i
  im = tif.imread(proofreads + i)
  out[k] = im
  # if out_is_there:
  #   out = np.dstack([out, im])
  # else:
  #   out = im
  #   out_is_there = True

print segs.shape
print gt.shape
print out.shape

print np.where(segs.ravel() != 0)
print np.where(gt.ravel() != 0)
print np.where(out.ravel() != 0)

tif.imsave('/tmp/pf0.tif', out[0].astype(np.uint32))


print 'VI groundtruth vs. proofread:', pc.variation_of_information(out.ravel(), gt.astype(np.uint32).ravel())