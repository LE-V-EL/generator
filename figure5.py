#
# updated from ian's original code
#   include ability to label individual stimuli (1,2,3,4)
#   change size to 256x256 for resnet training
#

import math
import numpy as np
import skimage.draw

class Figure5:

    SIZE = (100, 150)
    RANGE = (15, 90) #sizes of angles generated
    POS_RANGE = (20, 80) #position range
    POS_SCALE_MARKS = (20, 40, 60, 80)
    AUTO_SPOT_SIZE = 3 #how big automatic spot is in pixels
    LENGTH_MAX = 34 #how long a line can be for length
    LENGTH_MIN = 5 #lines disappear when they're too short
    ANGLE_LINE_LENGTH = 12 #how long the angle lines are
    AREA_DOF = 12 #maximum circle radius
    VOLUME_SIDE_MAX = 14
    CURV_DOF = 34
    CURV_WIDTH = 22 #auto curvature width
    WIGGLE = 5 #How many pixels of x "wiggling" it can do
    BACKGROUND_OBJECT = 5

    @staticmethod
    def calc_ranges(stimulus): #Calculates what the range of values is that "flags" supplies as a preset to other methods.
        R = 0 #Highest number that can be generated (range: 1-R)
        if stimulus is Figure5.angle:
            R = Figure5.RANGE[1] - Figure5.RANGE[0] + 1
        elif stimulus is Figure5.length:
            R = Figure5.LENGTH_MAX - Figure5.LENGTH_MIN + 1
        elif stimulus is Figure5.direction:
            R = 360
        elif stimulus is Figure5.area:
            R = Figure5.AREA_DOF
        elif stimulus is Figure5.volume:
            R = Figure5.VOLUME_SIDE_MAX
        elif stimulus is Figure5.curvature:
            R = Figure5.CURV_DOF
        elif stimulus is Figure5.position_non_aligned_scale or stimulus is Figure5.position_common_scale:
            R = Figure5.POS_RANGE[1] - Figure5.POS_RANGE[0] + 1
        return R 

    @staticmethod #for run_regression_isvetkey.py
    def _min(stimulus):
        if stimulus is Figure5.length:
            return Figure5.LENGTH_MIN
        elif stimulus is Figure5.position_non_aligned_scale or stimulus is Figure5.position_common_scale:
            return Figure5.POS_RANGE[0]
        return 1

    @staticmethod #for run_regression_isvetkey.py
    def _max(stimulus):
        if stimulus is Figure5.length:
            return Figure5.LENGTH_MAX
        elif stimulus is Figure5.position_non_aligned_scale or stimulus is Figure5.position_common_scale:
            return Figure5.POS_RANGE[1]
        return Figure5.calc_ranges(stimulus)


    @staticmethod #Driver method
    def flags(stimulus, flags): #flag 1: diagonal vs random, flag 2: x wiggle, flag 3: which is largest?
        sparse_ = [] #sparse of all stimuli
        label_ = [] #label of all stimuli
        parameters = 1 #number of permutations for all 4 combined
        X = 18
        XR = X
        if flags[1]:
            XR = X + np.random.randint((-1)*Figure5.WIGGLE, Figure5.WIGGLE)
            parameters *= (Figure5.WIGGLE*2+1)
        if flags[0]:
            Y = 20
        elif stimulus is not Figure5.position_common_scale and stimulus is not Figure5.position_non_aligned_scale:
            Y = np.random.randint(Figure5.POS_RANGE[0], Figure5.POS_RANGE[1])
            parameters *= (Figure5.POS_RANGE[1] - Figure5.POS_RANGE[0] + 1)

        R = Figure5.calc_ranges(stimulus)
        parameters *= (R**4)
        exclude_overlapping = []
        sizes = []
        if stimulus is Figure5.position_common_scale:
            while len(sizes) < 4:
                val =  np.random.randint(1, R)
                val += Figure5.POS_RANGE[0] - 1
                # since postion comon scale is on the same scale,
                # we need to make sure none are overlapping 
                if val not in exclude_overlapping:
                    sizes.append(val)
                    for exclude in range(val-3, val+4):
                        exclude_overlapping.append(exclude)
        else:
            sizes = [0] * 4
            for i in range(len(sizes)):
                sizes[i] = np.random.randint(1, R)
                if stimulus is Figure5.position_non_aligned_scale:
                    sizes[i] = sizes[i] + Figure5.POS_RANGE[0] - 1 #Fixes 1-61 to become 20-80
                elif stimulus is Figure5.angle:
                    sizes[i] = sizes[i] + Figure5.RANGE[0] - 1 # fizes 0--80 to become 10 - 90
                elif stimulus is Figure5.length:
                    sizes[i] += Figure5.LENGTH_MIN - 1
        # since they are on a common scale, they will be 
        if stimulus is Figure5.position_common_scale:
            sizes.sort()
        if flags[2]:
            L = sizes[0]
            SL = 0
            for i in range(1, len(sizes)):
                if sizes[i] > L:
                    L = sizes[i]
                    SL = i
            if SL > 0:
                sizes[0], sizes[SL] = sizes[SL], sizes[0]
            parameters = parameters / 4

        if stimulus is Figure5.position_non_aligned_scale:
            diff = np.random.randint(-9, 11)
            parameters *= 21
            temp = stimulus(X=XR, preset=sizes[0], recur=True, diff=diff, label_val=1)
        elif stimulus is Figure5.position_common_scale:
            temp = stimulus(preset=sizes[0], recur=True, label_val=1)
        else:
            temp = stimulus(X=XR, Y=Y, preset=sizes[0], recur=True)
        img = temp[1]
        sparse_.append(temp[0])
        label_.append(temp[2])
        if len(temp) > 3:
            parameters *= temp[3]

        for i in range(1, 4):
            X = XR = X + 38
            if flags[1]:
                XR = X + np.random.randint((-1)*Figure5.WIGGLE, Figure5.WIGGLE)
                parameters *= (Figure5.WIGGLE*2+1)
            if flags[0]:
                Y = Y + 20
            elif stimulus is not Figure5.position_common_scale and stimulus is not Figure5.position_non_aligned_scale:
                Y = np.random.randint(Figure5.POS_RANGE[0], Figure5.POS_RANGE[1])
                parameters *= (Figure5.POS_RANGE[1] - Figure5.POS_RANGE[0] + 1)
            if stimulus is Figure5.position_non_aligned_scale:
                diff = np.random.randint(-9, 11)
                temp = stimulus(X=XR, preset=sizes[i], preset_img=img, recur=True, diff=diff, label_val=i+1)
            elif stimulus is Figure5.position_common_scale:
                temp = stimulus(preset=sizes[i], preset_img=img, recur=True, label_val=i+1)
            else:
                temp = stimulus(X=XR, Y=Y, preset=sizes[i], preset_img=img, recur=True, label_val=i+1)
            sparse_.append(temp[0])
            label_.append(temp[2])
            if len(temp) > 3:
                parameters *= temp[3]
            #if parameters was an odd number (like 61^4) divided by 4, make it whole
            parameters = int(parameters)
        return sparse_, img, label_, parameters
    

    #FOR ALL STIMULUS METHODS
    #flags = the flags passed by the user (explanation in flags method)
    #X, Y = position of stimulus on image
    #preset = whatever is being randomized (direction, length, radius, etc)
    #preset_img = when it's the 2nd-4th stimulus being added to an existing image
    #recur = is it the user's call (false) or is it the flags method calling it (true)
    #Use of variable "recur" allows me to use methods as their own helper methods

    @staticmethod
    def position_non_aligned_scale(flags=[False, False, False], X=0, preset=None, preset_img=None, recur=False, diff=None, varspot=False, label_val=1):
        if not recur:
            return Figure5.flags(Figure5.position_non_aligned_scale, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)

        ORIGIN = X - 7 #where the line is
        if diff is not None:
            img = Figure5.add_scale(img, ORIGIN, diff=diff)
        else:
            diff = np.random.randint(-9, 11)
            img = Figure5.add_scale(img, ORIGIN, diff=diff)
        parameters = 1
        if varspot:
            sizes = [1, 3, 5, 7, 9, 11]
            spot_size = np.random.choice(sizes)
            parameters *= len(sizes)
        else:
            spot_size = Figure5.AUTO_SPOT_SIZE
        if preset is None:
            Y = np.random.randint(Figure5.POS_RANGE[0]+diff, Figure5.POS_RANGE[1]+diff)
        else:
            Y = preset
        Y = Y + diff
        label = Y - Figure5.POS_RANGE[0] - diff
        
        half_size = spot_size / 2
        img[int(Y-half_size):int(Y+half_size+1), int(X-half_size):int(X+half_size+1)] = label_val

        sparse = [Y, X, spot_size]

        return sparse, img, label, parameters

    @staticmethod
    def position_common_scale(flags=[False, False, False], preset=None, preset_img=None, recur=False, varspot=False, label_val=1):
        X = int(Figure5.SIZE[1] / 2)
        if not recur:
            return Figure5.flags(Figure5.position_common_scale, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)
            ORIGIN = X - 7 #where the line is
            img = Figure5.add_scale(img, ORIGIN)
        parameters = 1
        if varspot:
            sizes = [1, 3, 5, 7, 9, 11]
            spot_size = np.random.choice(sizes)
            parameters *= len(sizes)
        else:
            spot_size = Figure5.AUTO_SPOT_SIZE
        if preset is None:
            Y = np.random.randint(Figure5.POS_RANGE[0], Figure5.POS_RANGE[1])
        else:
            Y = preset
        label = Y - Figure5.POS_RANGE[0]
        
        half_size = spot_size / 2
        img[int(Y-half_size):int(Y+half_size+1), int(X-half_size):int(X+half_size+1)] = label_val

        sparse = [Y, X, spot_size]

        return sparse, img, label, parameters
    
    @staticmethod
    def add_scale(img, X, diff=0):
        img[Figure5.POS_RANGE[0]+diff:Figure5.POS_RANGE[1]+1+diff, X] = Figure5.BACKGROUND_OBJECT
        for i, mark in enumerate(Figure5.POS_SCALE_MARKS):
            img[mark+diff, X-2:X] = Figure5.BACKGROUND_OBJECT
            img[mark+diff, X - 4] = Figure5.BACKGROUND_OBJECT
            if i > 0:
                img[mark+diff-1, X - 4] = Figure5.BACKGROUND_OBJECT
            if i > 1:
                img[mark+diff+1, X - 4] = Figure5.BACKGROUND_OBJECT
            if i > 2:
                img[mark+diff,   X - 5] = Figure5.BACKGROUND_OBJECT
        return img


    @staticmethod
    def angle(flags=[False, False, False], X=0, Y=0, preset=None, preset_img=None, recur=False, label_val=1) :
        if not recur:
            return Figure5.flags(Figure5.angle, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)
        L = Figure5.ANGLE_LINE_LENGTH
        startangle = np.random.randint(0, 359)
        parameters = 360
        if preset is None:
            ANGLE = np.random.randint(Figure5.RANGE[0], Figure5.RANGE[1])
        else:
            ANGLE = preset
        t2 = startangle * (math.pi/180)
        diff2 = ANGLE * (math.pi/180)
        r, c = skimage.draw.line(Y, X, Y+(int)(L*np.sin(t2)), X+(int)(L*np.cos(t2)))
        diffangle = t2+diff2 #angle after diff is added (2nd leg)
        r2, c2 = skimage.draw.line(Y, X, Y+(int)(L*np.sin(diffangle)), X+(int)(L*np.cos(diffangle)))
        img[r, c] = label_val
        img[r2, c2] = label_val
        sparse = [Y, X, ANGLE, startangle]
        return sparse, img, ANGLE, parameters

    @staticmethod
    def length(flags=[False, False, False], X=0, Y=0, preset=None, preset_img=None, recur=False, label_val=1):
        if not recur:
            return Figure5.flags(Figure5.length, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)
        if preset is None:
            L = np.random.randint(1, Figure5.LENGTH_MAX)
        else:
            L = preset
        half_l = int(L * 0.5)
        img[Y-half_l:Y+half_l, X] = label_val
        sparse = [Y, X, L]
        return sparse, img, L

    @staticmethod
    def direction(flags=[False, False, False], X=0, Y=0, preset=None, preset_img=None, recur=False, label_val=1):
        if not recur:
            return Figure5.flags(Figure5.direction, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)
        L = Figure5.ANGLE_LINE_LENGTH
        if preset is None:
            angle = np.random.randint(0, 360)
        else:
            angle = preset
        radangle = angle * np.pi / 180
        r, c = skimage.draw.line(Y, X, Y+int(L*np.sin(radangle)), X+int(L*np.cos(radangle)))
        img[r,c] = label_val
        img[Y-1:Y+1, X-1:X+1] = label_val
        sparse = [Y, X, angle]
        return sparse, img, angle

    @staticmethod
    def area(flags=[False, False, False], X=0, Y=0, preset=None, preset_img=None, recur=False, label_val=1):
        if not recur:
            return Figure5.flags(Figure5.area, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)
        if preset is None:
            radius = np.random.randint(1, Figure5.AREA_DOF+1)
        else:
            radius = preset
        r, c = skimage.draw.ellipse_perimeter(Y, X, radius, radius)
        img[r, c] = label_val
        sparse = [Y, X, radius]
        label = np.pi * radius * radius
        return sparse, img, label

    @staticmethod
    def volume(flags=[False, False, False], X=0, Y=0, preset=None, preset_img=None, recur=False, label_val=1):
        if not recur:
            return Figure5.flags(Figure5.volume, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)

        if preset is None:
            depth = np.random.randint(1, Figure5.VOLUME_SIDE_MAX)
        else:
            depth = preset

        def obliqueProjection(point):
            angle = -45.
            alpha = (np.pi/180.0) * angle
            P = [[1, 0, (1/2.)*np.sin(alpha)], [0, 1, (1/2.)*np.cos(alpha)], [0, 0, 0]]
            ss = np.dot(P, point)
            return [int(np.round(ss[0])), int(np.round(ss[1]))]
        halfdepth = int(depth/2.)
        fbl = (Y+halfdepth, X-halfdepth)
        fbr = (fbl[0], fbl[1]+depth)
    
        r, c = skimage.draw.line(fbl[0], fbl[1], fbr[0], fbr[1])
        img[r, c] = label_val

        ftl = (fbl[0]-depth, fbl[1])
        ftr = (fbr[0]-depth, fbr[1])
        
        r, c = skimage.draw.line(ftl[0], ftl[1], ftr[0], ftr[1])
        img[r,c] = label_val
        r, c = skimage.draw.line(ftl[0], ftl[1], fbl[0], fbl[1])
        img[r, c] = label_val
        r, c = skimage.draw.line(ftr[0], ftr[1], fbr[0], fbr[1])
        img[r, c] = label_val

        bbr = obliqueProjection([fbr[0], fbr[1], depth])
        btr = (bbr[0]-depth, bbr[1])
        btl = (btr[0], btr[1]-depth)

        r, c = skimage.draw.line(fbr[0], fbr[1], bbr[0], bbr[1])
        img[r, c] = label_val
        r, c = skimage.draw.line(bbr[0], bbr[1], btr[0], btr[1])
        img[r, c] = label_val
        r, c = skimage.draw.line(btr[0], btr[1], btl[0], btl[1])
        img[r, c] = label_val
        r, c = skimage.draw.line(btl[0], btl[1], ftl[0], ftl[1])
        img[r, c] = label_val
        r, c = skimage.draw.line(btr[0], btr[1], ftr[0], ftr[1])
        img[r, c] = label_val

        sparse = [Y, X, depth]
        label = depth ** 3
        return sparse, img, label
        

    @staticmethod
    def curvature(flags=[False, False, False], X=0, Y=0, preset=None, preset_img=None, recur=False, varwidth=False, label_val=1):
        if not recur:
            return Figure5.flags(Figure5.curvature, flags)
        if preset_img is not None:
            img = preset_img
        else:
            img = np.zeros(Figure5.SIZE)
        if preset is None:
            depth = np.random.randint(1, Figure5.CURV_DOF)
        else:
            depth = preset
        width = Figure5.CURV_WIDTH
        parameters = 1
        halfwidth = int(width/2)
        if varwidth:
            width = np.random.randint(1, halfwidth)*2
            parameters = halfwidth
        start = (Y, X-halfwidth)
        mid = (Y-depth, X)
        end = (Y, X+halfwidth)
        r, c = skimage.draw.bezier_curve(start[0], start[1], mid[0], mid[1], end[0], end[1], 1)
        img[r, c] = label_val
        sparse = [Y, X, depth, width]
        t = 0.5
        P10 = (mid[0] - start[0], mid[1] - start[1])
        P21 = (end[0] - mid[0], end[1] - mid[1])
        dBt_x = 2*(1-t)*P10[1] + 2*t*P21[1]
        dBt_y = 2*(1-t)*P10[0] + 2*t*P21[0]
        dBt2_x = 2*(end[1] - 2*mid[1] + start[1])
        dBt2_y = 2*(end[0] - 2*mid[0] + start[0])
        curvature = np.abs((dBt_x*dBt2_y - dBt_y*dBt2_x) / ((dBt_x**2 + dBt_y**2)**(3/2.)))
        label = np.round(curvature, 3)
        return sparse, img, label, parameters
