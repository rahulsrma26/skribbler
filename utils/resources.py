import os
import cv2

PATH_RESOURCES = os.path.join(os.path.dirname(__file__), '..', 'resources')

def get_img(filename, mode=cv2.IMREAD_GRAYSCALE):
    filepath = os.path.join(PATH_RESOURCES, filename)
    if os.path.isfile(filepath):
        return cv2.imread(filepath, mode)
    raise ValueError(f'resource "{filepath}" not found')
