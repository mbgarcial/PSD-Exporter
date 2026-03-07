import pytest
import sys
sys.path.append("..")
import os
from psd_funcs import *
from psd_exporter import *

# TESTS for psd_funcs

# Process_psd() doesn't have a unit test, but all its internal helper functions work.
# dummy_process does basically the same and it works :)


# process_mask()
# needs: mask & kwargs
# returns: kwargs (with mask saved)
# use: updates kwargs["bbox"] & kwargs["alpha"] with mask info.
# uses: create_alpha()✅
# used by: process_psd

def test_process_mask():

    # init
    opened_psd   = open_psd("psd_test.psd")
    args         = get_export_args(**app_kwargs_init(opened_psd))
    psd          = opened_psd["psd"]
    # get mask
    mask = psd.find("group1").mask
    alpha = create_alpha(mask, (1024,1024))
   
    # No mask, returns same args
    assert process_mask(None,args) == args

    # if trim_to_mask, result["bbox"] == mask.bbox 
    args["trim_to_mask"] = True
    assert process_mask(mask,args)["bbox"] == mask.bbox

    #if bbox, keep the bbox
    args["trim_to_mask"] = False
    args["bbox"] = (0,0,200,200) 
    assert process_mask(mask,args)["bbox"] != mask.bbox

    # if no bbox, result["bbox"] == mask.bbox 
    args["trim_to_mask"] = False
    args["bbox"] = None
    assert process_mask(mask,args)["bbox"] == mask.bbox

    # result["alpha"] == create_alpha(mask, canvas_size)
    assert process_mask(mask,args)["alpha"] == alpha

    # if no canvas_size, result["alpha"] == create_alpha(mask, (mask.bbox[2],mask.bbox[3]))
    del args["canvas_size"]
    assert process_mask(mask,args)["alpha"] == create_alpha(mask, (mask.bbox[2],mask.bbox[3]))


# composite_alpha()
# needs: layer, alpha, canvas size
# returns: Image | None (on failure)
# use: composites a layer into an image, then extracts the alpha to create a mask, which then combines with the alpha given, and applies that to the image.
# used by : layer_to_image() ✅

def test_composite_alpha():
    # Init
    opened_psd  = open_psd("psd_test.psd")
    psd         = opened_psd["psd"]
    canvas_size = (1024,1024)
    layer       = psd.find("Layer2")
    # create alpha 
    alpha = create_alpha(psd.find("group1").mask, canvas_size) 

    # No layer|alpha == None
    assert composite_alpha(None,None,(800,600))==None
    assert composite_alpha(None,alpha,canvas_size)==None
    assert composite_alpha(layer,None,canvas_size)==None

    # layer.composite != composite_alpha. Size is !=
    layer_composite_img = layer.composite(force = True)
    composite_alpha_img = composite_alpha(layer,alpha,canvas_size)

    assert layer_composite_img != composite_alpha_img
    assert layer_composite_img.size != composite_alpha_img.size #type:ignore
    
    # alpha img is canvas size
    assert composite_alpha_img.size == canvas_size #type:ignore

    # Composite used inside composite_alpha is not the same as cpomposite_alpha , but both are canvas size
    img = layer.composite(force = True, viewport = tuple([0,0] + list(canvas_size)))
    assert img != composite_alpha_img
    assert img.size == composite_alpha_img.size #type:ignore
    
# create_alpha()
# needs: mask & canvas size
# returns: Image | None (on failure)
# use: returns a b/w image from the mask provided.
# uses: PIL funcs
# used by: process_mask()

def test_create_alpha():
    # Init
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    
    # get a group's mask
    mask        = psd.find("group1").mask
    canvas_size = (800,600)
    # create alpha 
    alpha = create_alpha(mask, canvas_size) 
   
    # if no mask, returns None
    assert create_alpha(None, canvas_size) == None
    # alpha size is canvas size provided
    assert alpha.size == canvas_size #type:ignore
    # alpha size not the same as the size of the mask
    assert mask.topil().convert("L").size != alpha.size #type:ignore
    # alpha size not the same as the size of the group either
    assert alpha.size != psd.find("group1").size #type:ignore

def test_layer_to_image_crop_to_mask():
    #Init
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)
    # Set to trim to mask
    args["trim_to_mask"] = True
    # Update args
    args       = get_export_args(**args)

    # Use a suitable layer
    layer_name  = "base"
    expimg      = ExportableImg(psd.find(layer_name), layer_name, "psd_test",**args)
    image       = layer_to_img(expimg.image,**expimg.get_args())

    # Make sure it matches the mask's bbox
    assert image.size == psd.find(layer_name).mask.size #type:ignore
    # Not the PSD visible size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    # It's not the same as the layer size
    assert image.size != psd.find("Layer1").size #type:ignore
    # It's not the same as canvas size
    assert image.size != args["canvas_size"] #type:ignore

def test_layer_to_image_trim_to_psd():
    # Init
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)
    # Set to trim visible
    args["trim_layers"]     = False
    args["trim_to_visible"] = True
    # Update the args
    args   = get_export_args(**args)
    # Get the psd's visible size from bbox
    psd_visible_size = (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1])

    # Use a suitable layer
    expimg = ExportableImg(psd.find("Layer1"), "Layer1", "psd_test",**args)
    image  = layer_to_img(expimg.image,**expimg.get_args())
    
    # Same as PSD visible size
    assert image.size == psd_visible_size #type:ignore
    # It's not the same as the layer size
    assert image.size != psd.find("Layer1").size #type:ignore
    # It's not the same as canvas size
    assert image.size != args["canvas_size"] #type:ignore

    # Try a diff layer
    expimg = ExportableImg(psd.find("base"), "base", "psd_test",**args)
    image  = layer_to_img(expimg.image,**expimg.get_args())
    
    assert image.size == psd_visible_size #type:ignore

def test_layer_to_image_no_trim():
    opened_psd   = open_psd("psd_test.psd")
    args         = get_export_args(**app_kwargs_init(opened_psd))
    psd          = opened_psd["psd"]
    layer        = psd.find("Layer1")
    args["bbox"] = tuple( [0,0] + list(args["canvas_size"]))

    expimg = ExportableImg(layer, "Layer1", "psd_test",**args)
    image  = layer_to_img(expimg.image,**expimg.get_args())
    
    # matches canvas size
    assert image.size == args["canvas_size"] #type:ignore
    # Not the PSD visible size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    # It's not the same as the layer size
    assert image.size != layer.size #type:ignore

def test_exportableimg_save_resize_noratio():
    # change "width" and "height", open saved image using PIL and make sure the size corresponds
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    args       = get_export_args(**app_kwargs_init(opened_psd))
    layer  = psd.find("base")

    args["width"] = 512
    args["height"] = 256
    args["scale"] = 1.1
    args["keep_aspect_ratio"] = False

    og_size = args["canvas_size"]
    w_scale = get_width_scale(og_size,args["width"])
    h_scale = get_height_scale(og_size,args["height"])

    expimg  = ExportableImg(layer, "base", "psd_test",**args)
    img     = layer_to_img(layer,**expimg.get_args())

    if check_image_exists(expimg.get_savepath()):
        os.remove(expimg.get_savepath())
    expimg.save()
    
    image = Image.open(expimg.get_savepath())

    assert image.size == (round(img.size[0]*w_scale),round(img.size[1]*h_scale))#type:ignore

def test_exportableimg_save_resize_keepratio():
    # change "scale", open saved image using PIL and make sure the size corresponds
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    args       = get_export_args(**app_kwargs_init(opened_psd))
    layer  = psd.find("base")
    
    args["scale"] = 0.5
    
    expimg = ExportableImg(layer, "base", "psd_test",**args)
    img    = layer_to_img(layer,**expimg.get_args())
    
    if check_image_exists(expimg.get_savepath()):
        os.remove(expimg.get_savepath())
    expimg.save()
    
    image = Image.open(expimg.get_savepath())
    assert int(image.size[0]) == int(img.size[0]*args["scale"])#type:ignore

def test_layer_to_image():
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    args       = get_export_args(**app_kwargs_init(opened_psd))
    layer  = psd.find("base")
    expimg = ExportableImg(layer, "base", "psd_test",**args)
   
    imgbase = layer_to_img(layer,**expimg.get_args())
    imgpsd  = layer_to_img(psd,**expimg.get_args())
    assert imgbase
    assert imgpsd
    assert imgbase.getbbox() == tuple([0,0]+list(layer.size))

def test_exportableimg_save():
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    args       = get_export_args(**app_kwargs_init(opened_psd))
    
    layer  = psd.find("base")
    expimg = ExportableImg(layer, "base", "psd_test",**args)
    
    exppsd = ExportableImg(psd, "psd_test","psd_test",**args)

    if check_image_exists(expimg.get_savepath()):
        os.remove(expimg.get_savepath())
    assert expimg.save()
    os.remove(expimg.get_savepath())

    if check_image_exists(exppsd.get_savepath()):
        os.remove(exppsd.get_savepath())
    assert exppsd.save()
    os.remove(exppsd.get_savepath())

def test_exportableimg_creation():
    
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    kwargs     = app_kwargs_init(opened_psd)
    args       = get_export_args(**kwargs)

    nolayer = psd.find("lala")
    with pytest.raises(ValueError):
        expimg = ExportableImg(nolayer, "base", "psd_test")#type:ignore

    layer  = psd.find("base")
    expimg = ExportableImg(layer, "base", "psd_test",**args) #type:ignore
    
    assert expimg.name == "base"
    assert expimg.path == "psd_test"
    assert expimg.ext == ".png"
    assert expimg.visible == True

    assert expimg.get_bbox() == layer.bbox #type:ignore
    assert expimg.get_savepath() == "psd_test/base.png"
    assert isinstance(expimg.get_args(),dict)
    
    args = expimg.get_args()
    assert args["bbox"] == layer.bbox #type:ignore
    assert args["width"] == psd.size[0]
    assert args["keep_aspect_ratio"] == True
    assert args["ignore_invisible"] == True

def test_check_image_exists():
    filepath = "psd_test.psd"
    assert check_image_exists(filepath) == True
    assert check_image_exists("psd_test.png") == False

def test_layer_repr():
    psd = PSDImage.open("psd_test.psd")
    layer = psd.find("base")
    repr = get_layer_repr([layer]) #type:ignore
    assert repr == "🎨 base ⏺\n"

    layer = psd.find("Layer1_clipping")
    repr = get_layer_repr([layer]) #type:ignore
    assert repr == "↷🫥🎨 Layer1_clipping\n"

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

# get_psd_dir()
def test_get_psd_dir():
    assert get_psd_dir("photo.psd") == "/"
    assert get_psd_dir("lala/photo.psd") == "lala/"
    assert get_psd_dir("lala/lele/") == "/"
    assert get_psd_dir("lala/lele/photo.png") == "/"

# get_scale(), get_width_scale(), get_height_scale()
def test_get_width_and_height_scale():
    size=(800,600)
    assert get_width_scale(size,400) == 0.5
    assert get_height_scale(size,300) == 0.5

def test_get_scale():
    size=(800,600)
    assert get_scale(size) == 1.0
    assert get_scale(size,400) == 0.5
    assert get_scale(size,200) == 0.25
    assert get_scale(size,200) != 0.5
    assert get_scale(size,100) == 0.125
    assert get_scale(size,height=300) == 0.5
    assert get_scale(size,height=150) == 0.25
    assert get_scale(size,height=75) == 0.125

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

# create_alpha(mask, canvas_size) -> Image.Image|None: converts a layer mask to b/w image to save on alpha channel
# composite_alpha(layer,alpha,canvas_size) -> Image.Image|None: Composites a layer and applies an alpha mask image to it
# process_psd() -> This is what saves the whole psd, by creating ExportableImages and saving them as it loops through all the files. It returns True if it manages to save everything, or a string if it fails
# process_mask()