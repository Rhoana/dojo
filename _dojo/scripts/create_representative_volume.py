import mahotas as mh
import os
import numpy as np
import matplotlib.pyplot as plt

groundtruth_path = os.path.join('/home/d//TMP/DOJO', 'isbi_train64_scf095_segs60_FS3_join500/labels')

tiles = os.listdir(groundtruth_path)
tiles = sorted(tiles)
out_is_there = False

for t in tiles:
    i = mh.imread(os.path.join(groundtruth_path, t), 'png')
    if out_is_there:
        out = np.dstack([out, i])
    else:
        out = i
        out_is_there = True
        


shape_x = 110
shape_y = 110
shape_z = 20

shape_x = out.shape[0]
shape_y = out.shape[1]
shape_z = out.shape[2]

size_x = 200
size_y = 200
size_z = 20

num_pixels = size_x * size_y * size_z
num_bins = 20
bin_size = num_pixels / num_bins
bins = [bin_size*i for i in range(num_bins)]

step_size_x = 1
step_size_y = 1
step_size_z = 1

num_steps_x = int(shape_x/step_size_x)
num_steps_y = int(shape_x/step_size_x)
num_steps_z = int(shape_x/step_size_x)

num_patches = num_steps_x * num_steps_y * num_steps_z
print num_patches*(num_bins-1)
features = np.zeros((num_patches,num_bins-1),dtype=np.uint32)
coordinates = np.zeros((num_patches,3),dtype=np.uint32)

i = 0
for x in range(0,shape_x-size_x,step_size_x):
    for y in range(0,shape_y-size_y,step_size_y):
        for z in range(0,shape_z-size_z, step_size_z):
            coordinates[i,0] = x
            coordinates[i,1] = y
            coordinates[i,2] = z
            
            sub_vol = out[x:x+size_x,y:y+size_y,z:z+size_z]
            sub_vol,_ = mh.labeled.relabel(sub_vol.astype(np.intc))            
            sub_sizes = mh.labeled.labeled_size(sub_vol)
            hist, _ = np.histogram(sub_sizes, bins=bins)
            
            
            features[i,:] = hist.astype(np.uint32)
            
            
            i += 1
            
            #print hist
            
centroid = np.mean(features,axis=0)

centroid_matrix = np.tile(centroid, (num_patches,1))

dist_squared_matrix = np.square(np.subtract(features, centroid_matrix))

dist_vector = np.sqrt(np.sum(dist_squared_matrix, axis=1))

min_i = dist_vector.argmin()

x = coordinates[min_i,0]
y = coordinates[min_i,1]
z = coordinates[min_i,2]
print x,y,z
sub_vol_repr = out[x:x+size_x,y:y+size_y,z:z+size_z]
# plt.imshow(np.squeeze(sub_vol_repr[:,:,0]))
