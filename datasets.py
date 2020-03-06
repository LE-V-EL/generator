import os, sys

# we need access to the MaskR-CNN code
sys.path.append(os.path.join(os.path.dirname(__file__), 'external/mask_rcnn/'))
from mrcnn import utils
from mrcnn import visualize

# we need access to Ian's code
sys.path.append(os.path.join(os.path.dirname(__file__), 'external/ian/'))
from figure5 import Figure5

import numpy as np
import json
from operator import add, sub
from datetime import datetime
from statistics import mean 
import pickle

class PartitionedDataset:

    class AngleDataset(utils.Dataset):

        def __init__(self, p_dataset, count):
            '''
            '''
            # allow the inner class to access the outer class's data
            self.p_dataset = p_dataset
            self.count = count
            self.label_distribution = []
            super().__init__()


        def generate(self):
            '''
            '''
            SETNAME = 'stimuli'
            
            self.add_class(SETNAME, 1, "angle")

            for i in range(self.count):

                sparse, mask, angles, parameters = self.next_image()

                img = mask.copy()
                img[img>0] = 1 # re-set to binary
                self.add_image(SETNAME, image_id=i, path=None,
                              image=img, sparse=sparse, parameters=parameters,
                              mask=mask,
                              angles=angles)

                
        def load_image(self, image_id):
            '''
            '''
            info = self.image_info[image_id]

            image = info['image']
            
            loaded_img_3D = np.stack((image,)*3, -1)
            
            return (loaded_img_3D*255).astype(np.uint8)
            
                
        def load_mask(self, image_id):
            '''

            '''
            info = self.image_info[image_id]
            mask = info['mask']
            
            mask2 = np.zeros((mask.shape[0],mask.shape[1], 4), dtype=np.uint8)

            for i in range(0,4):
                filtered_mask = mask.copy()
                filtered_mask[filtered_mask!=(i+1)] = 0
                filtered_mask[filtered_mask==(i+1)] = 1
                mask2[:,:, i] = filtered_mask
            
            return mask2, np.array([1,1,1,1]) # it is always class 1 but four times 
                                            # and each channel of the mask needs to have a single angle
        
        
        def random_image(self):
            '''
            '''
            
            return Figure5.angle(self.p_dataset.flags)



        def next_image(self):
            '''
            '''
            
            sparse, mask, angles, parameters = self.random_image()

            # so we can use the nice numpy operations
            label = np.asarray(angles)
            
            self.p_dataset.add_itteration()
            
            while not self.validate_label(label):
                
                sparse, mask, angles, parameters = self.random_image()
                
                label = np.asarray(angles)
                
                self.p_dataset.add_itteration()

            self.add_label(label)

            return sparse, mask, angles, parameters



        def validate_label(self, label):
            '''
            '''
            return self.p_dataset.check_label_euclid(label) and self.check_distribution(label)



        def check_distribution(self, label):
            '''
            '''

            # we dont care until we reach larger amounts
            if sum(self.label_distribution) < 1000:
                return True
            
            # not adding anything over 110% of the mean amount in each angle bucket
            threshold = mean(self.label_distribution) * 1.1
            
            for element in label:
                
                if element > len(self.label_distribution):
                    
                    self.extend_label_distribution(element)
                    
                    # recalculate after extending
                    threshold = mean(self.label_distribution) * 1.1


                if self.label_distribution[element - 1] > threshold:
                    return False
            
            return True



        def extend_label_distribution(self, element):
            '''
            '''
            
            while len(self.label_distribution) < element:
                self.label_distribution.append(0)



        def add_label(self, label):
            '''
            '''

            for element in label:
                
                if element > len(self.label_distribution):
                    self.extend_label_distribution(element)

                self.label_distribution[element - 1] += 1

            self.p_dataset.add_label(label)



        @staticmethod
        def show(which, howmany=4):
            '''
            '''

            image_ids = np.random.choice(which.image_ids, howmany)
            for image_id in image_ids:
                image = which.load_image(image_id)
                mask, class_ids = which.load_mask(image_id)
                visualize.display_top_masks(image, mask, class_ids, which.class_names)

    #####################################################################################
    #
    #####################################################################################

    def __init__(self, 
        counts             = {"train": 500, "val": 50, "test": 50}, 
        flags              = [True,False,False], 
        distance_threshold = 5.0,
        naive              = False,
        to_file            = True):
        '''
        '''

        self.counts = counts
        self.flags = flags
        self.distance_threshold = distance_threshold
        self.naive = naive
        self.to_file = to_file

        self.__dataset = {}
        self.labels = []
        self.euclid_table = {}
        self.itterations = 0


    def generate(self):

        startTime = datetime.now()

        for key in self.counts:

            if self.to_file:
                dataset = self.AngleDataset(self, self.counts[key])
                dataset.generate()
                dataset.prepare()
                dataset.p_dataset = None
                with open(key + ".p", "wb") as file:
                    pickle.dump(dataset, file)

            else:
                self.__dataset[key] = self.AngleDataset(self, self.counts[key])
                self.__dataset[key].generate()
                self.__dataset[key].prepare()

            print("Finished Generating: ", key)

        print("Evaluation time ", datetime.now() - startTime)



    def dataset(self, name):
        '''
        '''
        return self.__dataset[name]



    def check_label_euclid(self, label):

        if self.naive:
            return self.check_label_euclid_naive(label)
        else:
            return self.check_label_euclid_memo(label)


    def check_label_euclid_naive(self, label, label_set=None, print_failure=False):
        '''
        '''
        if label_set is None:
            label_set = self.labels

        for existing_label in label_set:
            dist = np.linalg.norm(existing_label - label)
            if dist < self.distance_threshold:
                if print_failure:
                    print("Naive Validation Failure")
                    print("Label to Add :", label)
                    print("Existing Label: ", existing_label)
                return False
        return True



    def check_label_euclid_memo(self, label):
        
        return not self.euclid_table.get("-".join(label.astype(str)))



    def validate_labels(self):
        for index in range(len(self.labels) - 1):

            if not index % 1000:
                print("validating: ", index)

            if not self.check_label_euclid_naive(self.labels[index], self.labels[index + 1:], print_failure=True):
                return False
        
        return True


    def add_label(self, label):
        '''
        '''
        self.labels.append(label)

        if not len(self.labels) % 1000:
            print("labels: ", len(self.labels))
        
        if not self.naive:
            self.add_labels_within_threshold(label)



    def add_labels_within_threshold(self, label):
        self.__add_labels_within_threshold(label, label, 0, 0)



    def __add_labels_within_threshold(self, base_label, current_label, index, old_dist):

        for op in [add, sub]:

            dist = old_dist

            next_label = current_label.copy();

            while dist < self.distance_threshold:


                self.add_euclid_label(next_label)

                if index + 1 < len(base_label):
                    self.__add_labels_within_threshold(base_label, next_label.copy(), index + 1, dist)

                next_label[index] = op(next_label[index], 1)

                dist = np.linalg.norm(base_label - next_label)



    def add_euclid_label(self, label):

        self.euclid_table["-".join(label.astype(str))] = True



    def add_itteration(self):
        self.itterations += 1
        if not self.itterations % 1000:
            print("itteration: ", self.itterations)



