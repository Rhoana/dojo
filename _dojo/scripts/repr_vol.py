import mahotas as mh
import os
import numpy as np
import matplotlib.pyplot as plt
import tifffile as tif


groundtruth_path = os.path.join('train-labels.tif')

vol = tif.imread(groundtruth_path)


shape_x = vol.shape[2]
shape_y = vol.shape[1]
shape_z = vol.shape[0]


# shape_x = 220
# shape_y = 220
# shape_z = 40

# patch size
size_x = 200
size_y = 200
size_z = 10

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
#print num_patches*(num_bins-1)
features = np.zeros((num_patches,num_bins-1),dtype=np.uint32)
coordinates = np.zeros((num_patches,3),dtype=np.uint32)

i = 0
for x in range(0,shape_x-size_x,step_size_x):
    for y in range(0,shape_y-size_y,step_size_y):
        for z in range(0,shape_z-size_z, step_size_z):
            coordinates[i,2] = x
            coordinates[i,1] = y
            coordinates[i,0] = z
            
            sub_vol = vol[z:z+size_z,y:y+size_y,x:x+size_x]
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

x = coordinates[min_i,2]
y = coordinates[min_i,1]
z = coordinates[min_i,0]
print x,y,z
sub_vol_repr = vol[z:z+size_z,y:y+size_y,x:x+size_x]
