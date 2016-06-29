import os
import math
import PIL
import PIL.Image
import lxml
import lxml.etree
import numpy as np


class Imgo:
    def __init__(self, img, output_dir):

        img = np.array(img).astype(np.uint8)
        shape = img.shape

        tile_num_pixels_y = 512
        tile_num_pixels_x = 512

        output_tile_image_path     = os.path.join(output_dir,'images/tiles/')
        output_tile_volume_file    = os.path.join(output_dir,'images/tiledVolumeDescription.xml')

        output_image_extension     = '.tif'
        image_resize_filter        = PIL.Image.ANTIALIAS

        nimages_to_process            = shape[2]
        original_image_num_pixels_x, original_image_num_pixels_y = shape[:2]

        for tile_index_z in range(nimages_to_process):

            original_image = PIL.Image.fromarray(img[:,:,tile_index_z])

            current_image_num_pixels_y = original_image_num_pixels_y
            current_image_num_pixels_x = original_image_num_pixels_x
            current_tile_data_space_y  = tile_num_pixels_y
            current_tile_data_space_x  = tile_num_pixels_x
            tile_index_w               = 0

            while current_image_num_pixels_y > tile_num_pixels_y / 2 or current_image_num_pixels_x > tile_num_pixels_x / 2:

                current_tile_image_path    = output_tile_image_path     + os.sep + 'w=' + '%08d' % ( tile_index_w ) + os.sep + 'z=' + '%08d' % ( tile_index_z )

                self.mkdir_safe( current_tile_image_path )

                current_image = original_image.resize( ( current_image_num_pixels_x, current_image_num_pixels_y ), image_resize_filter )

                num_tiles_y = int( math.ceil( float( current_image_num_pixels_y ) / tile_num_pixels_y ) )
                num_tiles_x = int( math.ceil( float( current_image_num_pixels_x ) / tile_num_pixels_x ) )

                for tile_index_y in range( num_tiles_y ):
                    for tile_index_x in range( num_tiles_x ):

                        y = tile_index_y * tile_num_pixels_y
                        x = tile_index_x * tile_num_pixels_x

                        current_tile_image_name = current_tile_image_path + os.sep + 'y=' + '%08d' % ( tile_index_y ) + ','  + 'x=' + '%08d' % ( tile_index_x ) + output_image_extension

                        tile_image = current_image.crop( ( x, y, x + tile_num_pixels_x, y + tile_num_pixels_y ) )
                        tile_image.save( current_tile_image_name )
                        print current_tile_image_name
                        print

                current_image_num_pixels_y = current_image_num_pixels_y / 2
                current_image_num_pixels_x = current_image_num_pixels_x / 2
                current_tile_data_space_y  = current_tile_data_space_y  * 2
                current_tile_data_space_x  = current_tile_data_space_x  * 2
                tile_index_w               = tile_index_w + 1

            tile_index_z = tile_index_z + 1

            if tile_index_z >= nimages_to_process:
                break

        #Output TiledVolumeDescription xml file
        tiledVolumeDescription = lxml.etree.Element( "tiledVolumeDescription",
            fileExtension = output_image_extension[1:],
            numTilesX = str( int( math.ceil( original_image_num_pixels_x / tile_num_pixels_x ) ) ),
            numTilesY = str( int( math.ceil( original_image_num_pixels_y / tile_num_pixels_y ) ) ),
            numTilesZ = str( tile_index_z ),
            numTilesW = str( tile_index_w ),
            numVoxelsPerTileX = str( tile_num_pixels_x ),
            numVoxelsPerTileY = str( tile_num_pixels_y ),
            numVoxelsPerTileZ = str( 1 ),
            numVoxelsX = str( original_image_num_pixels_x ),
            numVoxelsY = str( original_image_num_pixels_y ),
            numVoxelsZ = str( tile_index_z ),
            dxgiFormat = 'R8_UNorm',
            numBytesPerVoxel = str( 1 ),
            isSigned = str( False ).lower() )

        with open( output_tile_volume_file, 'w' ) as file:
            file.write( lxml.etree.tostring( tiledVolumeDescription, pretty_print = True ) )

    def mkdir_safe(self, dir_to_make ):

        os.makedirs(dir_to_make)
