#!/opt/local/bin/python2.7

import cv
import cv2
import numpy as np

import sys
from lib.histgram import Histgram

# load file
if(len(sys.argv) != 3):
    print 'usage: python %s input.jpg output.jpg' % sys.argv[0]
    quit()

infile  = sys.argv[1]
outfile = sys.argv[2]

try:
    img = cv2.imread(infile, 1)
except:
    print 'fail to load %s' % infile
    quit()

# contrastive
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

hist = Histgram(gray)
gray = hist.normalize_img(gray)

# digitalize image
_,thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)

# a little bit magic..
dilate   = cv2.dilate(adaptive, None)
erode    = cv2.erode(dilate, None)

# write
cv2.imwrite(outfile, erode)

