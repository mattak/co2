import cv2
import util

class Histgram:
    """ this is image histgram class """
    def __init__(self, img):
        self.img = img
        self.calc()
    
    def calc(self):
        if self.img.ndim != 2:
            print "dim is %d" % self.img.ndim
            raise "array dimention must be 2" % self.img.ndim

        width  = self.img[0].size
        height = self.img.size / width

        print 'width %s , height %s' % (width, height)
        
        self.bin = [0] * 256
        
        for y in range(height):
            for x in range(width):
                v = self.img[y, x]
                self.bin[v] += 1

    def flatten_range(self):
        newbin = [0] * len(self.bin)

        # cut off less 1%
        cutoff = int(max(self.bin) * 0.01)
        for i in range(len(self.bin)):
            newbin[i] = 0 if self.bin[i] < cutoff else self.bin[i]

        # calc min, max
        (min_p, max_p) = (0, 255)
        range_bin = range(len(self.bin))
        for i in range_bin:
            if newbin[i] == 0:
                min_p = i
            else:
                break

        range_bin.reverse()
        for i in range_bin:
            if newbin[i] == 0:
                max_p = i
            else:
                break

        return (min_p, max_p)
        
    def normalize_rule(self, from_range, to_range):
        (f1, f2) = from_range
        (t1, t2) = to_range
        A = float(t2 - t1) / (f2 - f1)

        print '%f' % (A)
        cnv_bin = [0] * 256

        for i in range(256):
            v = int(A * (i - f1))
            if v < 0:
                cnv_bin[i] = 0
            elif v > 255:
                cnv_bin[i] = 255
            else:
                cnv_bin[i] = v

        return cnv_bin

        # f1,f2 -> t1,t2
        # size = (t2-t1) / (f2-f1) * (x - f1)

    def normalize_bin(self):
        (min_p, max_p) = self.flatten_range()
        print 'minp maxp : %d %d' % (min_p, max_p)

        rule = self.normalize_rule((min_p, max_p), (0, 255))
        tmp_bin = [0] * (len(rule))

        for i in range(len(self.bin)):
            print '%d -> %d : %d -> %d' % (i, rule[i], self.bin[i], self.bin[rule[i]])
            tmp_bin[rule[i]] = self.bin[i]
        for i in range(len(self.bin)):
            self.bin[i] = tmp_bin[i]

        (minp, maxp) = self.flatten_range()
        print "minp, maxp : %d %d" % (minp, maxp)

    def normalize_img(self, img):
        (min_p, max_p) = self.flatten_range()
        rule = self.normalize_rule((min_p, max_p), (0, 255))

        if img.ndim != 2:
            raise 'dimention must be 2'

        width  = img[0].size
        height = img.size / width

        for y in range(height):
            for x in range(width):
                img[y, x] = rule[img[y,x]]
        
        return img


    def show(self):
        print self.bin

        ch = cw = 320
        mx = max(self.bin)
        sh = float(ch) / float(mx)
        sw = float(cw) / float(256)
        print "sh %f sw %f" % (sh, sw)
        
        color = 255
        canvas = np.zeros((ch, cw), np.uint8)
        canvas[:] = 255
        for i in range(255):
            x1 = int(i * sw)
            x2 = int((i+1) * sw)
            y1 = int(ch -self.bin[i] * sh)
            y2 = ch
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0,0,0), -1)

        imgshow(canvas)

