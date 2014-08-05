import nibabel
import tifffile as tif

path = '/Users/d/Stuff'
outpath = '/Users/d/Stuff/'


vol = path + '/orig.tif'
seg = path + '/aparcaseg.nii'

volume = tif.imread(vol)

for v in range(volume.shape[0]):

  tif.imsave(outpath + 'image/' + str(v) + '.tif', volume[v])

label = nibabel.load(seg)
label = label.get_data()

for l in range(volume.shape[0]):

  tif.imsave(outpath + 'label/' + str(l) + '.tif', label[:,:,l].transpose())

