import tifffile as tif
import mahotas as mh
import numpy as np
import h5py
import sys
import os
import shutil

# groundtruth
images_f = 'train-input.tif'
labels_f = 'train-labels.tif'

images = tif.imread(images_f)
labels = tif.imread(labels_f)

# segmentation
seg_dir = '../isbi_train64_scf095_segs60_FS3_join500/labels/'
segs = np.zeros((64,1024,1024), dtype=np.uint32)
for s in sorted(os.listdir(seg_dir)):
  z = int(s.split('.')[0])
  segs[z] = mh.imread(seg_dir + s)




#
# ROI
#
x = 0
y = 0
z = 0
dim_x = 400
dim_y = 400
dim_z = 10

out_images = np.zeros((dim_z,dim_y,dim_x), dtype=images.dtype)
out_labels = np.zeros((dim_z,dim_y,dim_x), dtype=labels.dtype)
out_segs = np.zeros((dim_z,dim_y,dim_x), dtype=segs.dtype)

out_images[0:dim_z, 0:dim_y, 0:dim_x] = images[z:z+dim_z, y:y+dim_y, x:x+dim_x]
out_labels[0:dim_z, 0:dim_y, 0:dim_x] = labels[z:z+dim_z, y:y+dim_y, x:x+dim_x]
out_segs[0:dim_z, 0:dim_y, 0:dim_x] = segs[z:z+dim_z, y:y+dim_y, x:x+dim_x]

tif.imsave('cut-train-input.tif', out_images)
tif.imsave('cut-train-labels.tif', out_labels)
tif.imsave('cut-train-segs.tif', out_segs)


# store separate slices
shutil.rmtree('segs',True)
os.mkdir('segs')
for z in range(dim_z):
  tif.imsave('segs/'+str(z)+'.tif',out_segs[z].astype(np.uint32))

shutil.rmtree('images',True)
os.mkdir('images')
for z in range(dim_z):
  tif.imsave('images/'+str(z)+'.tif',out_images[z])

shutil.rmtree('truth',True)
os.mkdir('truth')
for z in range(dim_z):
  tif.imsave('truth/'+str(z)+'.tif',out_labels[z])

   
os.system('python /home/d/Projects/Mojo/Mojo.2.0/Mojo/Tools/MojoImportTools/ImageTileCalculator.py')
os.system('python /home/d/Projects/Mojo/Mojo.2.0/Mojo/Tools/MojoImportTools/SegmentationTileCalculator.py')

