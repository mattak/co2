#!/opt/local/bin/python2.7
# -*- coding: utf-8 -*-

import sys
import cv2 as cv
import numpy as np
import config
import lib.util as util

# load file
if(len(sys.argv) != 2):
    print 'usage: python %s input.jpg' % sys.argv[0]
    quit()

infile  = sys.argv[1]
src     = cv.imread(infile, 0)

# config file
template_images = config.template.keys()

# step1. detect img
class Detector:
    def __init__(self, templates):
        self.templates = {}
        for file in templates: #range(len(self.templates)):
            self.templates[file] = cv.imread(file, 0)

            if self.templates[file] == None:
                print "load fail: %s" % file
                raise "load error"

    def is_maximum_around(self, area, center, points, exclude_patch):
        (ew, eh) = exclude_patch
        (cx, cy) = center

        for i in range(len(points)):
            (px, py) = points[i]

            if px >= cx - ew and px <= cx + ew and\
               py >= cy - eh and py <= cy + eh:

                if area[cy, cx] < area[py, px]: 
                    return False

                elif area[cy, cx] == area[py, px]:
                    if cx > px or (cx == px and cy > py):
                        return False

        return True

    def sheet2point(self, sheet, thresh=200, exclude_patch=(20,20)):
        eh, ew = exclude_patch
        width  = sheet[0].size
        height = sheet.size / width
        candinate_points = []

        # pickup points
        for y in range(height):
            for x in range(width):
                if sheet[y,x] >= thresh:
                    candinate_points.append((x,y))

        # summerize points
        result_points = []
        for p in candinate_points:
            if self.is_maximum_around(sheet, p, candinate_points, exclude_patch):
                result_points.append(p)

        return result_points

    def point2area(self, points, shape):
        areas = []
        for p in points:
            areas.append((p[0], p[1], p[0]+shape[1], p[1]+shape[0]))
        return areas

    def detect_sheet(self, target, patch):
        result      = cv.matchTemplate(target, patch, cv.TM_CCOEFF_NORMED)
        val, result = cv.threshold(result, 0.01, 0, cv.THRESH_TOZERO)
        result8     = cv.normalize(result, None, 0, 255, cv.NORM_MINMAX, cv.CV_8U)
        return result8

    def l1_mean(self, target, template, p):
        (h1, w1) = target.shape
        (h2, w2) = template.shape

        y1 = p[1]
        y2 = p[1] + h2
        x1 = p[0]
        x2 = p[0] + w2

        y2 = h1 if (y2 > h1) else y2
        x2 = w1 if (x2 > w1) else x2

        h = y2 - y1
        w = x2 - x1

        sum = long(0)
        for y in range(h):
            for x in range(w):
                v1 = long(target[y1 + y, x1 + x])
                v2 = long(template[y,x])
                sum += long(abs(v1 - v2))

        mean = float(sum) / (h * w)
        return mean

    def calc_overrap_area(self, area1, area2):
        # 50% overraping
        # area = (x1,y1,x2,y2)
        if area1[0] <= area2[0]:
            x1 = area2[0]
            x2 = area1[2]
        else:
            x1 = area1[0]
            x2 = area2[2]

        if area1[1] <= area2[1]:
            y1 = area2[1]
            y2 = area1[3]
        else:
            y1 = area1[1]
            y2 = area2[3]

        if x1 > x2 or y1 > y2:
            return 0

        ratio = float((x2 - x1) * (y2 - y1)) / ((area1[2] - area1[0]) * (area1[3] - area1[1]))
        return ratio

    def exclude_detection(self, target, hash_results):
        new_result = {}

        # calc template distance
        for file in hash_results.keys():
            template = self.templates[file]
            areas    = hash_results[file]
            new_result[file] = {}

            for area in areas:
                val = self.l1_mean(target, template, (area[0], area[1]))
                new_result[file][area] = val

        # calc inner
        inner_passed = {}
        for file in new_result.keys():
            areas = new_result[file].keys()
            inner_passed[file] = {}

            for i in range(len(areas)):
                area1 = areas[i]
                val1  = new_result[file][area1]

                ok    = True
                for j in range(len(areas)):
                    if i == j:
                        continue
                    area2 = areas[j]
                    val2  = new_result[file][area2]
                    ratio = self.calc_overrap_area(area1, area2)

                    if ratio > 0.3 and val1 > val2:
                        ok = False
                if ok:
                    inner_passed[file][area1] = val1
        print "inner"
        print inner_passed

        # calc outer
        outer_passed = {}
        files = inner_passed.keys()

        for i in range(len(files)):
            file1 = files[i]
            areas1 = inner_passed[file1].keys()
            outer_passed[file1] = []
            ok = True

            for area1 in areas1:
                val1 = inner_passed[file1][area1]

                for j in range(i+1, len(files)):
                    file2 = files[j]
                    areas2 = inner_passed[file2].keys()

                    for area2 in areas2:
                        val2  = new_result[file2][area2]
                        ratio = self.calc_overrap_area(area1, area2)

                        if ratio > 0.3 and val1 > val2:
                            ok = False
                if ok:
                    outer_passed[file1].append(area1)

        return outer_passed

    def detect(self, target):
        result_hash = {}

        for file in self.templates.keys():
            template = self.templates[file]
            sheet  = self.detect_sheet(target, template)
            points = self.sheet2point(sheet)
            areas  = self.point2area(points, template.shape)

            result_hash[file] = areas
            #exclude_detection(target, template, hash_results)
        print result_hash
        result_hash = self.exclude_detection(target, result_hash)
        print result_hash
        for file in result_hash.keys():
            print file
            self.show_detect(target, result_hash[file])
        #


    def show_detect(self, target, areas):
        canvas = np.copy(target)

        for area in areas:
            p1 = (area[0], area[1])
            p2 = (area[2], area[3])
            cv.rectangle(canvas, p1, p2, (0,0,0), 2)

        util.imgshow(canvas)

detector = Detector(template_images)
detector.detect(src)

# step2. create string



