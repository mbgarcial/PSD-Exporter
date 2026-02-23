# Please make new tests!
import pytest
import sys
sys.path.append("..")
from psd_funcs import *
from psd_exporter import *

# TESTS for psd_funcs

def test_is_selected_false():
    psd = PSDImage.open("psd_test.psd")
    layer = psd.find("base")

    #No layer
    assert is_selected(None, []) == False
    assert is_selected(None, ["base"]) == False

    # no selection
    assert is_selected(layer,[]) == False

    #name not in selection strings
    assert is_selected(layer,["group1"]) == False
    assert is_selected(layer,["Layer1","attr1"]) == False
    
    #name and parent not in selection tuples
    assert is_selected(layer,[("base","group1")]) == False
    assert is_selected(layer,[("group1","Root")]) == False
  
    #name doesn't match pattern
    assert is_selected(layer,["*bas"]) == False
    assert is_selected(layer, ["ase*"]) == False
    assert is_selected(layer,["*j*"]) == False
    assert is_selected(layer,["*ae*"]) == False
    assert is_selected(layer,["*be*"]) == False
    assert is_selected(layer,["a*"]) == False
    assert is_selected(layer,["*s"]) == False
    assert is_selected(layer,["*a*e_"]) == False

    # name doesn't match anything
    assert is_selected(layer,[("Layer1","group2"),"attr1","*ojos"]) == False
    assert is_selected(layer,[("base","group1"),"*_","Layer1"]) == False

def test_is_selected_true():
    psd = PSDImage.open("psd_test.psd")
    layer = psd.find("base")

    #name in selection
    assert is_selected(layer,["base"]) == True
    assert is_selected(layer,["layer1","base"]) == True

    #name and parent in selection
    assert is_selected(layer,[("base","Root")]) == True
    assert is_selected(layer,[("base","Root"),"*__","layer1"]) == True

    #name matches pattern
    assert is_selected(layer,["*base"]) == True
    assert is_selected(layer, ["base*"]) == True
    assert is_selected(layer,["*base*"]) == True
    assert is_selected(layer,["*se"]) == True
    assert is_selected(layer, ["ba*"]) == True
    assert is_selected(layer,["*ba*"]) == True
    assert is_selected(layer,["ba*se"]) == True
    assert is_selected(layer,["*ba*se*"]) == True
    assert is_selected(layer,["b*e"]) == True
    assert is_selected(layer,["*b*e"]) == True
    assert is_selected(layer,["b*e*"]) == True
    assert is_selected(layer,["*as*"]) == True
    assert is_selected(layer,["b*as*e"]) == True
    assert is_selected(layer,["*"]) == True


def test_get_regex():
    assert get_regex(["layer1","layer2"]) == r"(^layer1$|^layer2$)"
    assert get_regex(["*1","layer2"]) == r"(1$|^layer2$)"
    assert get_regex(["*1","2*"]) == r"(1$|^2)"
    assert get_regex(["layer*"]) == r"(^layer)"
    assert get_regex(["e-*","*clipping","*test*"]) == r"(^e-|clipping$|test)"
    assert get_regex(["claire*_mo"]) == r"(^claire.*_mo$)"


def test_what_do():
    psd = PSDImage.open("psd_test.psd")
    layer = psd.find("base")

    # Selection includes layer
    assert what_do(layer,["base"],[],"ignore") == "ignore" #ignoring selected
    assert what_do(layer,["base"],[],"export") == "save" # exporting selected
    assert what_do(layer,["base"]) == "save" # exporting selected

    # No selection
    assert what_do(layer) == "save" # exporting selected 
    assert what_do(layer,selected_action="ignore") == "save" # ignoring selected 

    # Selection doesn't include layer
    assert what_do(layer, ["group1"]) == "ignore" # exporting selected
    assert what_do(layer, ["group1"], selected_action="ignore") == "save" # ignoring selected
    
    # Selection includes "all"
    assert what_do(layer,["*"]) == "save" # exporting selected 
    assert what_do(layer, ["group1", "*"]) == "save" # exporting selection
    assert what_do(layer, ["group1", "*"], selected_action="ignore") == "ignore" # ignoring selection


def test_what_do_group():
    psd = PSDImage.open("psd_test.psd")
    layer = psd.find("group1")

    #Testing flatten.
    assert what_do(layer,[],["group1"],None,"flatten") == "save"
    assert what_do(layer,[],["group1"],None,"ignore") == "pass"
    assert what_do(layer,[],["group2"],None,"ignore") == "save"

    # Selection includes layer
    assert what_do(layer,["group1"],[],"ignore") == "ignore" #ignoring selected
    assert what_do(layer,["group1"],[],"export") == "export" # exporting selected
    assert what_do(layer,["group1"]) == "export" # exporting selected

    # No selection
    assert what_do(layer) == "pass" # exporting selected 
    assert what_do(layer,selected_action="ignore") == "pass" # ignoring selected 

    # Selection doesn't include layer
    assert what_do(layer, ["group2"]) == "pass" # exporting selected
    assert what_do(layer, ["group2"], selected_action="ignore") == "pass" # ignoring selected
    
    # Selection includes "all"
    assert what_do(layer,["*"]) == "export" # exporting selected 
    assert what_do(layer, ["group2", "*"]) == "export" # exporting selection
    assert what_do(layer, ["group2", "*"], selected_action="ignore") == "ignore" # ignoring selection


#filter layers - dummy process testing 
def test_dummy_process_flatten_action():
    psd = PSDImage.open("psd_test.psd")
    
    assert dummy_process(psd,["group2"], "ignore", ["group1"], None) == [("base","Root"),("group1","Root")]
    assert dummy_process(psd,[], None, ["group*"], None) == [("base","Root"),("group1","Root"),("group2","Root")]
    assert dummy_process(psd,[], None, ["group1", "attr3"], None) == [("base","Root"),("group1","Root"),("attr3","group2")]
    assert dummy_process(psd,["b*"], "ignore", ["group*"], "ignore") == [("attr1","group1"),("attr2","group1"),("attr3","group2")]
    assert dummy_process(psd,["b*"], "ignore", ["attr*"], "ignore") == [("group1","Root"),("group2","Root")]

def test_dummy_process_ignore():
    psd = PSDImage.open("psd_test.psd")
    selected = ["b*"]
    flatten = ["group*"]
    assert dummy_process(psd,selected,"ignore",flatten) == [("group1","Root"),("group2","Root")]
    selected = ["*layer*"]
    flatten = []
    assert dummy_process(psd,selected,"ignore",flatten) == [("base","Root"),("attr1","group1"),("attr2","group1")]
    selected = ["group1","group2"]
    assert dummy_process(psd,selected,"ignore",flatten) == [("base","Root")]
    selected = ["group2"]
    assert dummy_process(psd,selected,"ignore",flatten) == [("base","Root"),("attr1","group1"),("attr2","group1")]

def test_dummy_process_flatten():
    psd = PSDImage.open("psd_test.psd")
    selected = ["b*"]
    flatten = ["group1"]
    assert dummy_process(psd,selected,"export",flatten) == [("base","Root"),("group1","Root")]
    flatten = ["group2"]
    assert dummy_process(psd,selected,"export",flatten) == [("base","Root"),("group2","Root")]
    flatten = ["group*"]
    assert dummy_process(psd,flatten,"export",flatten) == [("group1","Root"),("group2","Root")]
    selected=["attr*"]
    assert dummy_process(psd,selected,"export",flatten) == [("group1","Root"),("group2","Root")]
    flatten = ["attr3"]
    assert dummy_process(psd,selected,"export",flatten) == [("attr1","group1"),("attr2","group1"),("attr3","group2")]

def test_dummy_process_export_filters():
    psd = PSDImage.open("psd_test.psd")
    selected=["b*"]
    assert dummy_process(psd,selected,"export") == [("base","Root")]
    selected=["Layer*"]
    exp = dummy_process(psd,selected,"export")
    assert set(exp) == set([("Layer1","attr3"),("Layer2","attr3")])
    selected=["*1"]
    exp = dummy_process(psd,selected,"export")
    assert set(exp) == set([("Layer1","attr3"),("attr1","group1"),("attr2","group1")])

def test_dummy_process_export():
    psd = PSDImage.open("psd_test.psd")
    # export only selected
    assert dummy_process(psd,["base"],"export") == [("base","Root")]
    assert dummy_process(psd,["group1"],"export") == [("attr1","group1"),("attr2", "group1")]
    exp =  dummy_process(psd,["group2"],"export")
    assert set(exp) == set([("Layer2","attr3"), ("Layer1", "attr3")])
    assert dummy_process(psd,["base","group1"],"export") == [("base","Root"),("attr1","group1"),("attr2", "group1")]
    


# MAY NOT BE USED
def test_get_all_layernames():

    psd = PSDImage.open("psd_test.psd")
    layers = get_all_layernames(psd)
    layernames = [layer[0] for layer in layers]
    assert "base" in layernames
    assert "lala" not in layernames
    assert "group1" in layernames
    assert "attr1" in layernames
    assert ("attr1", "group1") in layers
    assert ("attr2","group1") in layers
    assert ("Layer1","attr3") in layers
    assert ("layer5","attr4") not in layers
    assert ("base", "Root") in layers
    
    base = psd.find("base")
    assert base.parent.name == "Root" #type:ignore

# open_psd()
def test_open_psd():
    psd = PSDImage.open("psd_test.psd")
    assert open_psd("psd_test.psd")["psd"].size == psd.size
    assert open_psd("psd_test.psd")["psd_name"] == "psd_test.psd"
    assert open_psd("psd_test.psd")["psd_size"] == (1024,1024)

# get_psd_dir()
def test_get_psd_dir():
    assert get_psd_dir("photo.psd") == "/"
    assert get_psd_dir("lala/photo.psd") == "lala/"
    assert get_psd_dir("lala/lele/") == "/"
    assert get_psd_dir("lala/lele/photo.png") == "/"

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



# Functions that we can test

# AUX

# get_height_scale(og_size,new_height)->float:
# get_width_scale(og_size,new_width)->float:
# get_scale(size:tuple[int,int], width=None, height=None)-> float: returns a float that corresponds what % of the og width/heigh is the given width/height

# get_layer_repr(layers:list[Layer], level=0)->str: returns Layer name if layer is Layer, it iterates over itself appending names if it's a group. It add emojis too!

# get_export_args(**kwargs) -> dict: returns relevant kwargs for process.psd. Assigns default values and adjusts others.

# check_image_exists(filepath)-> bool : Checks if an image file exists

# layer_to_img(layer:Layer|PSDImage, **kwargs) -> Image.Image | None: Composites a Layer/PSDImage and returns an image. Returns None if the image creation fails
# create_alpha(mask, canvas_size) -> Image.Image|None: converts a layer mask to b/w image to save on alpha channel
# composite_alpha(layer,alpha,canvas_size) -> Image.Image|None: Composites a layer and applies an alpha mask image to it
# class ExportableImg() -> this is a layer/group/psdimg and has a lot of methods
# process_psd() -> This is what saves the whole psd, by creating ExportableImages and saving them as it loops through all the files. It returns True if it manages to save everything, or a string if it fails