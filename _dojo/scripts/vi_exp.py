import partition_comparison as pc
import mahotas as mh
import tifffile as tif
import os
import numpy as np
from sklearn import metrics

segs = tif.imread('/home/d/TMP/DOJO/mojo_400_5_orig/cut-train-segs.tif')
gt = tif.imread('/home/d/TMP/DOJO/mojo_400_5_orig/cut-train-labels.tif')


exp = tif.imread('/home/d/dong.tif')

exp[exp==0] = 2000

# crop the data to only image data
x = 210
y = 60
z = 50 # we dont need since we have already cut the z
dim_x = dim_y = 400
segs = segs[:,y:y+dim_y,x:x+dim_x]
gt = gt[:,y:y+dim_y,x:x+dim_x]
#out = out[:,y:y+dim_y,x:x+dim_x]


print 'VI groundtruth vs. groundtruth:', pc.variation_of_information(gt.astype(np.uint32).ravel(), gt.astype(np.uint32).ravel())
print 'VI groundtruth vs. pipeline:',pc.variation_of_information(gt.astype(np.uint32).ravel(), segs.ravel())
# print 'VI groundtruth vs. proofread:', pc.variation_of_information(gt.astype(np.uint32).ravel(), out.ravel())
print 'VI groundtruth vs. expert:', pc.variation_of_information(gt.astype(np.uint32).ravel(), exp.astype(np.uint32).ravel())

print 'Adjusted RandIndex groundtruth vs. groundtruth:', metrics.adjusted_rand_score(gt.astype(np.uint32).ravel(), gt.astype(np.uint32).ravel())
print 'Adjusted RandIndex groundtruth vs. pipeline:', metrics.adjusted_rand_score(gt.astype(np.uint32).ravel(), segs.ravel())
# print 'Adjusted RandIndex groundtruth vs. proofread:', metrics.adjusted_rand_score(gt.astype(np.uint32).ravel(), out.ravel())
print 'Adjusted RandIndex groundtruth vs. expert:', metrics.adjusted_rand_score(gt.astype(np.uint32).ravel(), exp.astype(np.uint32).ravel())
