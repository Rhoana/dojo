import os
import sys
import glob
import mahotas
import numpy as np
import csv
import h5py
import tifffile as tif

min_2d_seg_size = 500
min_3d_seg_size = 2000
rot = 0

gt_folder = sys.argv[1]
seg_parent_folder = sys.argv[2]

output_path = sys.argv[-1]

if len(sys.argv) > 4:
    min_2d_seg_size = int(sys.argv[3])

if len(sys.argv) > 5:
    min_3d_seg_size = int(sys.argv[4])

if len(sys.argv) > 6:
    rot = int(sys.argv[5])

def load_stack(folder_name):

    stack = None
    input_files = sorted(glob.glob(os.path.join(folder_name, '*')))

    for i, file_name in enumerate(input_files):

        print file_name

        if file_name.endswith('h5') or file_name.endswith('hdf5'):
            infile = h5py.File(file_name)
            im = infile['/probabilities'][...]
        else:
            im = mahotas.imread(file_name)
            if len(im.shape) == 3:
                im = np.uint32(im[ :, :, 0 ]) + np.uint32(im[ :, :, 1 ]) * 2**8 + np.uint32(im[ :, :, 2 ]) * 2**16

        if im.shape[0] > 400:
            im = im[60:60+400, 210:210+400]

        if rot != 0:
            im = np.rot90(im, rot)

        if stack is None:
            stack = np.zeros((len(input_files), im.shape[0], im.shape[1]), dtype=im.dtype)
            print 'Stack size={0}, dtype={1}.'.format(stack.shape, stack.dtype)
        stack[i,:,:] = im

        #print file_name

    return stack

def count_errors(gt_folder, seg_folder):
    # Load volumes

    gt_stack = load_stack(gt_folder)
    seg_stack = load_stack(seg_folder)

    gt_ids = np.unique(gt_stack.ravel())
    seg_ids = np.unique(seg_stack.ravel())

    # count 2d split operations required
    split_count_2d = 0
    for seg_id in seg_ids:
        if seg_id == 0:
            continue
        for zi in range(seg_stack.shape[0]):
            gt_counts = np.bincount(gt_stack[zi,:,:][seg_stack[zi,:,:]==seg_id])
            if len(gt_counts) == 0:
                continue
            gt_counts[0] = 0
            gt_counts[gt_counts < min_2d_seg_size] = 0
            gt_objects = len(np.nonzero(gt_counts)[0])
            if gt_objects > 1:
                split_count_2d += gt_objects - 1

    # count 3d split operations required
    split_count_3d = 0
    for seg_id in seg_ids:
        if seg_id == 0:
            continue
        gt_counts = np.bincount(gt_stack[seg_stack==seg_id])
        if len(gt_counts) == 0:
            continue
        gt_counts[0] = 0
        gt_counts[gt_counts < min_3d_seg_size] = 0
        gt_objects = len(np.nonzero(gt_counts)[0])
        if gt_objects > 1:
            split_count_3d += gt_objects - 1

    # count 3d merge operations required
    merge_count = 0
    for gt_id in gt_ids:
        if gt_id == 0:
            continue
        seg_counts = np.bincount(seg_stack[gt_stack==gt_id])
        if len(seg_counts) == 0:
            continue
        seg_counts[0] = 0
        seg_counts[seg_counts < min_3d_seg_size] = 0
        seg_objects = len(np.nonzero(seg_counts)[0])
        if seg_objects > 1:
            merge_count += seg_objects - 1

    print "{0} 2D Split or {1} 3D Split and {2} 3D Merge operations required.".format(split_count_2d, split_count_3d, merge_count)

    return (split_count_2d, split_count_3d, merge_count)

seg_folders = glob.glob(os.path.join(seg_parent_folder, '*tif'))
print 'aaa',seg_folders

results = np.zeros((3,len(seg_folders)), dtype=np.int64)
for i, seg_folder in enumerate(seg_folders):
    print seg_folder
    counts = count_errors(gt_folder, seg_folder)
    results[0,i] = counts[0]
    results[1,i] = counts[1]
    results[2,i] = counts[2]

# Output results
output_csvfile = open(output_path, 'wb')
outwriter = csv.writer(output_csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
outwriter.writerow(['Trial',
    '2D Splits Required (minsize={0})'.format(min_2d_seg_size),
    '3D Splits Required (minsize={0})'.format(min_3d_seg_size),
    '3D Merges Required (minsize={0})'.format(min_3d_seg_size)])
for i, seg_folder in enumerate(seg_folders):
    outwriter.writerow([os.path.split(seg_folder)[-1].replace('tif',''), results[0,i], results[1,i], results[2,i]])
output_csvfile.close()

