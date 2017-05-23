import os
import math
import cv2
import lxml
import lxml.etree
import numpy as np


class Imgo:
    def __init__(self, output_dir):

        self.tile_num_pixels_y = 512
        self.tile_num_pixels_x = 512

        self.output_tile_image_path     = os.path.join(output_dir,'images/tiles/')
        self.output_tile_volume_file    = os.path.join(output_dir,'images/tiledVolumeDescription.xml')

        self.output_image_extension     = '.tif'


    def run(self,original_image,tile_index_z):

        ( original_image_num_pixels_x, original_image_num_pixels_y ) = original_image.shape

        current_image_num_pixels_y = original_image_num_pixels_y
        current_image_num_pixels_x = original_image_num_pixels_x
        current_tile_data_space_y  = self.tile_num_pixels_y
        current_tile_data_space_x  = self.tile_num_pixels_x
        self.tile_index_z          = tile_index_z
        self.tile_index_w          = 0

        while current_image_num_pixels_y > self.tile_num_pixels_y / 2 or current_image_num_pixels_x > self.tile_num_pixels_x / 2:

            current_tile_image_path    = self.output_tile_image_path     + os.sep + 'w=' + '%08d' % ( self.tile_index_w ) + os.sep + 'z=' + '%08d' % ( self.tile_index_z )

            self.mkdir_safe( current_tile_image_path )

            current_image = cv2.resize(original_image,( current_image_num_pixels_x, current_image_num_pixels_y ))

            num_tiles_y = int( math.ceil( float( current_image_num_pixels_y ) / self.tile_num_pixels_y ) )
            num_tiles_x = int( math.ceil( float( current_image_num_pixels_x ) / self.tile_num_pixels_x ) )

            for tile_index_y in range( num_tiles_y ):
                for tile_index_x in range( num_tiles_x ):

                    y = tile_index_y * self.tile_num_pixels_y
                    x = tile_index_x * self.tile_num_pixels_x

                    current_tile_image_name = current_tile_image_path + os.sep + 'y=' + '%08d' % ( tile_index_y ) + ','  + 'x=' + '%08d' % ( tile_index_x ) + self.output_image_extension

                    tile_image = current_image[y:y + self.tile_num_pixels_y, x:x + self.tile_num_pixels_x]
                    cv2.imwrite( current_tile_image_name , tile_image)
                    print current_tile_image_name

            current_image_num_pixels_y = current_image_num_pixels_y / 2
            current_image_num_pixels_x = current_image_num_pixels_x / 2
            current_tile_data_space_y  = current_tile_data_space_y  * 2
            current_tile_data_space_x  = current_tile_data_space_x  * 2
            self.tile_index_w               = self.tile_index_w + 1

    def save(self,all_shape):

        ( original_image_num_pixels_x, original_image_num_pixels_y, numTilesZ) = all_shape

        #Output TiledVolumeDescription xml file
        tiledVolumeDescription = lxml.etree.Element( "tiledVolumeDescription",
            fileExtension = self.output_image_extension[1:],
            numTilesX = str( int( math.ceil( original_image_num_pixels_x / self.tile_num_pixels_x ) ) ),
            numTilesY = str( int( math.ceil( original_image_num_pixels_y / self.tile_num_pixels_y ) ) ),
            numTilesZ = str( numTilesZ ),
            numTilesW = str( self.tile_index_w ),
            numVoxelsPerTileX = str( self.tile_num_pixels_x ),
            numVoxelsPerTileY = str( self.tile_num_pixels_y ),
            numVoxelsPerTileZ = str( 1 ),
            numVoxelsX = str( original_image_num_pixels_x ),
            numVoxelsY = str( original_image_num_pixels_y ),
            numVoxelsZ = str( numTilesZ ),
            dxgiFormat = 'R8_UNorm',
            numBytesPerVoxel = str( 1 ),
            isSigned = str( False ).lower() )

        with open( self.output_tile_volume_file, 'w' ) as file:
            file.write( lxml.etree.tostring( tiledVolumeDescription, pretty_print = True ) )

    def mkdir_safe(self, dir_to_make ):

        os.makedirs(dir_to_make)
