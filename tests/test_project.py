import pytest
import sys
sys.path.append("..")
from psd_funcs import *
from project import *

# test for project.py

def test_find_single_layer():
    psd = PSDImage.open("psd_test.psd")
    assert find_single_layer(psd,"base") == psd.find("base")
    assert find_single_layer(psd, "Layer1") ==  psd.find("Layer1")
    assert find_single_layer(psd, "attr1") == "There's more than one Layer with the name 'attr1'."
    assert find_single_layer(psd, "attr5") == "Layer 'attr5' not found."
    assert find_single_layer(psd, "group1") == "'group1' is a group."

def test_get_layer_repr():
    psd = PSDImage.open("psd_test.psd")
    layer = psd.find("base")
    repr = get_layer_repr([layer]) #type:ignore
    assert repr == "🎨 base ⏺\n"

    layer = psd.find("Layer1_clipping")
    repr = get_layer_repr([layer]) #type:ignore
    assert repr == "↷🫥🎨 Layer1_clipping\n"

# get_export_args()
def test_get_export_args():
    psd = open_psd("psd_test.psd")
    kwargs = app_kwargs_init(psd)
    args = get_export_args(**kwargs)

    assert args["extension"] == ".png"
    assert args["ignore_invisible"] == True
    assert args["scale"] == 1.0
    assert args["canvas_size"] == kwargs["file"]["psd_size"]

    assert args["bbox"] == None

    kwargs["trim_layers"] = False
    kwargs["trim_to_visible"] = True
    args = get_export_args(**kwargs)
    assert args["bbox"] == kwargs["file"]["psd"].bbox

    kwargs["trim_layers"] = False
    kwargs["trim_to_visible"] = False
    args = get_export_args(**kwargs)

    assert args["bbox"] == tuple([0,0] + list(args["canvas_size"]))
    
# open_psd()
def test_open_psd():
    psd = PSDImage.open("psd_test.psd")
    opened_psd = open_psd("psd_test.psd")
    assert opened_psd["psd"].size == psd.size
    assert opened_psd["psd_name"] == "psd_test.psd"
    assert opened_psd["psd_size"] == (1024,1024)

#get_resize()
def test_get_resize():
    size = (800,600)

    with pytest.raises(ValueError):
        get_resize(size)

    # percent returns same percent
    assert get_resize(size, width=100) == 100
    assert get_resize(size, height=50) == 50

    # pixels returns the proportional other size
    assert get_resize(size, kind="px", width=1920) == 1440
    assert get_resize((1280,720), kind="px", height=1080) == 1920

    # convert % to px
    assert get_resize(size, width=100, convert=True) == 800
    assert get_resize(size, height=50, convert=True) == 300

    # convert px to %
    assert get_resize(size, width = 800, kind="px", convert=True) == 100
    assert get_resize(size, height = 300, kind="px", convert=True) == 50
    
def test_size_convert():
    size = (800,600)
    # convert to %
    assert size_convert(size,(800,600), "%") == (100,100)
    assert size_convert(size,(400,150), "%") == (50,25)

    # convert to px
    assert size_convert(size,(100,100), "px") == (800,600)
    assert size_convert(size,(10,100), "px") == (80,600)

    # back and forth
    a = size_convert(size, (100,100), "px")
    assert size_convert(size,a,"%") == (100,100)

    a = size_convert(size,(400,150),"px")
    assert size_convert(size,a,"%") == (400,150)

