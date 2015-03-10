import cv2
import numpy as np
import sys


factor = int(sys.argv[2])


img = cv2.imread(sys.argv[1], cv2.CV_LOAD_IMAGE_GRAYSCALE)
# img = cv2.resize(img, (16384/factor, 16384/factor))
# cv2.imwrite('/tmp/subcv.jpg', img)
