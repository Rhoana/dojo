import cv2
import numpy as np
import sys


factor = int(sys.argv[2])

out = np.zeros((16384/factor,16384/factor), dtype=np.uint8)


img = cv2.imread(sys.argv[1], cv2.CV_LOAD_IMAGE_GRAYSCALE)

k = 0
l = 0

for i in range(16384):
  if i % factor == 0:

    for j in range(16384):
      if j % factor == 0:

        out[k][l] = img[i][j]

        l += 1

    l = 0
    k += 1

cv2.imwrite('/tmp/subplain.jpg', out)
