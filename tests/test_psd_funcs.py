# Please make new tests!
import pytest
import sys
sys.path.append("..")
from psd_funcs import *
from psd_exporter import *

# TESTS for psd_funcs

#get_resize()
def test_get_resize():
    size = (800,600)

    with pytest.raises(ValueError):
        get_resize(size)

    # percent returns same percent
    assert get_resize(size,width=100) == 100
    assert get_resize(size,height=50) == 50

    # pixels returns the proportional other size
    assert get_resize(size, kind="px", width=1920) == 1440
    assert get_resize((1280,720), kind="px", height=1080) == 1920

    # convert % to px
    assert get_resize(size,width=100, convert=True) == 800
    assert get_resize(size,height=50, convert=True) == 300

    # convert px to %
    assert get_resize(size, width = 800, kind="px", convert=True) == 100
    assert get_resize(size, height = 300, kind="px", convert=True) == 50
    
def test_size_convert():
    size = (800,600)
    # convert to %
    assert size_convert(size,(800,600), kind="%") == (100,100)
    assert size_convert(size,(400,150), kind="%") == (50,25)

    # convert to px
    assert size_convert(size,(100,100), kind="px") == (800,600)
    assert size_convert(size,(10,100), kind="px") == (80,600)

    # back and forth
    a = size_convert(size,(100,100), kind="px")
    assert size_convert(size,a,kind="%") == (100,100)
    a = size_convert(size,(400,150), kind="px")
    assert size_convert(size,a,kind="%") == (400,150)





    

# Functions that we can test

# AUX

# get_height_scale(og_size,new_height)->float:
# get_width_scale(og_size,new_width)->float:
# get_scale(size:tuple[int,int], width=None, height=None)-> float: returns a float that corresponds what % of the og width/heigh is the given width/height
# get_percent(size:tuple[int,int], width=None, height=None)-> int: Same as scale, but returns the rounded %, not a float.
# get_size(size:tuple[int,int], percent:float, width=False, height=False)->int: get new rounded width or height given a size tuple and a % percent
# get_size_from_ratio(ratio:float, width=None, height=None) -> int: get new height or width given an aspect ratio and the other size element
# get_psd_ratio(psd:PSDImage)->float: return the image ratio (width/height)
# get_repr(psd:PSDImage)->str: PSD Layer structure as a string
# get_layer_repr(layers:list[Layer], level=0)->str: returns Layer name if layer is Layer, it iterates over itself appending names if it's a group. It add emojis too!

# get_psd_filename_from_path(filename:str) -> str: Given a string that's a path to a file, this function returns a string with the name of the file (extension included). Uses regex!
# open_psd(filename:str) -> dict: opens a PSD file from a path str and returns a dict with a PSDImage object and its name (filename.psd). It also saves size.
# def get_export_args(**kwargs) -> dict: returns relevant kwargs for process.psd. Assigns default values and adjusts others.

# check_image_exists(filepath)-> bool : Checks if an image file exists
# should_ignore_layer(layer:Layer,**kwargs): checks if a layer should be ignored via kwargs
# layer_to_img(layer:Layer|PSDImage, **kwargs) -> Image.Image | None: Composites a Layer/PSDImage and returns an image. Returns None if the image creation fails
# create_alpha(mask, canvas_size) -> Image.Image|None: converts a layer mask to b/w image to save on alpha channel
# composite_alpha(layer,alpha,canvas_size) -> Image.Image|None: Composites a layer and applies an alpha mask image to it
# class ExportableImg() -> this is a layer/group/psdimg and has a lot of methods
# process_psd() -> This is what saves the whole psd, by creating ExportableImages and saving them as it loops through all the files. It returns True if it manages to save everything, or a string if it fails