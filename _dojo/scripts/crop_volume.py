import os
import tifffile as tif
import mahotas
from PIL import Image as PILImage
import numpy
import sqlite3

def crop_volume(dir, outdir, x, y, w, h):


    files = os.listdir(dir)

    for f in files:

        if (f.startswith('.')):
            continue

        i = PILImage.open(os.path.join(dir,f))
        # i = tif.imread(os.path.join(dir,f))
        i = numpy.array(i)
        cropped = i[y:y+h,x:x+w]

        tif.imsave(os.path.join(outdir,f+'.tif'), cropped)



# crop_volume('/tmp/images/','/tmp/images_tif_cropped/', 2130-512, 3321-512, 1024, 1024)


def recolor_volume(dir, outdir, database_file):

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM relabelMap')
    result = cursor.fetchall()

    mergeTable = {}
    for r in result:
        mergeTable[r[0]] = r[1:]

    print 'loaded colortable.'
    # print mergeTable

    files = os.listdir(dir)

    for f in files:

        if (f.startswith('.')):
            continue

        i = tif.imread(os.path.join(dir,f))

        for oldid in mergeTable.keys():
            i[i==oldid] = mergeTable[oldid]

        tif.imsave(os.path.join(outdir,f), i)


#recolor_volume('/tmp/ids_tif_cropped/', '/tmp/ids_tif_cropped_recolored/', '/tmp/ids/segmentInfo.db')


def relabel_volume(dir, outdir):


    files = sorted(os.listdir(dir))

    out = None
    out_is_there = False

    for f in files:

        i = tif.imread(os.path.join(dir,f))
        if (out_is_there):
            out = numpy.dstack([out, i])

        else:
            out = i
            out_is_there = True


    print '3d volume', out.shape

    import skimage
    from skimage.segmentation import relabel_sequential

    relabeled,fm,im = skimage.segmentation.relabel_sequential(out)

    print 'Max', relabeled.max()

    for z in range(relabeled.shape[2]):
        tif.imsave(os.path.join(outdir,str(z)+'.tif'),relabeled[:,:,z].astype(numpy.uint32))
        print 'stored', z

relabel_volume('/tmp/ids_tif_cropped_recolored', '/tmp/ids_tif_cropped_recolored_relabeled/')