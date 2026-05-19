
import pytest
import sys
sys.path.append("..")
import os
from psd_funcs import *
from project import *

# TESTS for psd_funcs

# Process_psd() doesn't have a unit test, but all its internal helper functions work.

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

def test_layer_to_img_crop_bbox():
    # test that when we have crop as true, it crops the image to the specified bbox
    opened_psd = open_psd("psd_test2.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)

    layer_name  = "Layer 2"
    layer       = psd.find(layer_name)

    crop_bbox   = (0,0,250,600)

    args["crop"]= True
    args["bbox"]= crop_bbox
    args        = get_export_args(**args)

    expimg = ExportableImg(layer, layer_name, "psd_test2",**args)
    image  = layer_to_img(expimg.image,**expimg.get_args())

    # image size is crop box size
    assert image.size == (crop_bbox[2]-crop_bbox[0],crop_bbox[3]-crop_bbox[1]) #type: ignore
    # img size is not layer size
    assert image.size != layer.size #type:ignore
    # img size is not canvas size
    assert image.size != args["canvas_size"] #type:ignore
    # image size is not full visible psd size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore

def test_layer_to_img_trim_each_no_trim_visible():
    # test that when we do trim each layer, a layer that's bigger than canvas size gets trimmed to canvas size
    # use psd_test2.psd
    #Init
    opened_psd = open_psd("psd_test2.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)
    args       = get_export_args(**args)

    # Use a suitable layer
    layer_name  = "Layer 2"
    layer       = psd.find(layer_name)
    trim_layer_bbox = trim_oob_bbox(layer.bbox,list(psd.size) )
    trim_layer_size =  (trim_layer_bbox[2]-trim_layer_bbox[0],trim_layer_bbox[3]-trim_layer_bbox[1])

    # ---test 1 : trim each WITHOUT oob trim
    
    args["trim_to_size"]    = False
    args["trim_layers"]     = True
    args["trim_to_visible"] = False
    expimg     = ExportableImg(layer, layer_name, "psd_test2",**args)
    image      = layer_to_img(expimg.image,**expimg.get_args())

    # ✅ layer bbox != trimmed layer bbox
    assert layer.bbox != trim_layer_bbox #type:ignore
    # image size IS layer size
    assert layer.size == image.size #type:ignore
    # image size is NOT trimmed layer size
    assert image.size != trim_layer_size #type:ignore
    # image size is not canvas size
    assert image.size != args["canvas_size"] #type:ignore

    # image size is not full visible psd size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    
def test_layer_to_img_trim_each_trim_visible():
    # test that when we do trim each layer, a layer that's bigger than canvas size gets trimmed to canvas size
    # use psd_test2.psd
    #Init
    opened_psd = open_psd("psd_test2.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)
    

    # Use a suitable layer
    layer_name  = "Layer 2"
    layer       = psd.find(layer_name)
    trim_layer_bbox = trim_oob_bbox(layer.bbox,list(psd.size) )
    trim_layer_size =  (trim_layer_bbox[2]-trim_layer_bbox[0],trim_layer_bbox[3]-trim_layer_bbox[1])

    # ---test 2 : trim each with oob trim
   
    args["trim_to_size"] = True
    args["trim_layers"]  = True
    args["trim_to_visible"] = False

    args       = get_export_args(**args)
    expimg     = ExportableImg(layer, layer_name, "psd_test2",**args)
    image      = layer_to_img(expimg.image,**expimg.get_args())

    # ✅ layer bbox != trimmed layer bbox
    assert layer.bbox != trim_layer_bbox #type:ignore
    # ✅ image size is not layer size
    assert layer.size != image.size #type:ignore
    # ✅ image size is trimmed layer size
    assert image.size == trim_layer_size #type:ignore
    # ✅image size is not canvas size
    assert image.size != args["canvas_size"] #type:ignore
    # ✅image size is not full visible psd size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore

def test_layer_to_img_trim_full_trim_visible():
    # test that when we do trim each layer, a layer that's bigger than canvas size gets trimmed to canvas size
    # use psd_test2.psd
    #Init
    opened_psd = open_psd("psd_test2.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)

    

    # Use a suitable layer
    layer_name  = "Layer 2"
    layer       = psd.find(layer_name)
    trim_layer_bbox = trim_oob_bbox(layer.bbox,list(psd.size) )
    trim_layer_size =  (trim_layer_bbox[2]-trim_layer_bbox[0],trim_layer_bbox[3]-trim_layer_bbox[1])

    # -- test 3: trim full with oob trim

    args["trim_to_size"]    = True
    args["trim_layers"]     = False
    args["trim_to_visible"] = True

    args       = get_export_args(**args)
    
    expimg     = ExportableImg(layer, layer_name, "psd_test2",**args)
    image      = layer_to_img(expimg.image,**expimg.get_args())
    #
    # image size is NOT layer size
    assert image.size != layer.size #type:ignore
    #  image size is NOT trimmed layer size
    assert image.size != trim_layer_size #type:ignore
    # image size is NOT canvas size
    assert image.size != args["canvas_size"] #type:ignore
    # image size is NOT full visible psd size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    
def test_layer_to_img_trim_full_no_trim_visible():
    # test that when we do trim each layer, a layer that's bigger than canvas size gets trimmed to canvas size
    # use psd_test2.psd
    #Init
    opened_psd = open_psd("psd_test2.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)
    

    # Use a suitable layer
    layer_name  = "Layer 2"
    layer       = psd.find(layer_name)
    trim_layer_bbox = trim_oob_bbox(layer.bbox,list(psd.size) )
    trim_layer_size =  (trim_layer_bbox[2]-trim_layer_bbox[0],trim_layer_bbox[3]-trim_layer_bbox[1])

    # -- test 4: trim full WITHOUT oob trim

    args["trim_to_size"]    = False
    args["trim_layers"]     = False
    args["trim_to_visible"] = True

    args       = get_export_args(**args)
    expimg      = ExportableImg(layer, layer_name, "psd_test2",**args)
    image       = layer_to_img(expimg.image,**expimg.get_args())
    
    # ✅ layer bbox == trimmed layer bbox
    assert layer.bbox != trim_layer_bbox #type:ignore
    # ✅ image size is NOT layer size
    assert image.size != layer.size #type:ignore
    # ✅image size is NOT trimmed layer size
    assert image.size != trim_layer_size #type:ignore
    # ✅image size is not canvas size
    assert image.size != args["canvas_size"] #type:ignore
    # ✅image size IS full visible psd size
    assert image.size == (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    
def test_layer_to_img_no_trim_trim_visible():
    # test that when we do trim each layer, a layer that's bigger than canvas size gets trimmed to canvas size
    # use psd_test2.psd
    #Init
    opened_psd = open_psd("psd_test2.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)
    

    # Use a suitable layer
    layer_name  = "Layer 2"
    layer       = psd.find(layer_name)
    trim_layer_bbox = trim_oob_bbox(layer.bbox,list(psd.size) )
    trim_layer_size =  (trim_layer_bbox[2]-trim_layer_bbox[0],trim_layer_bbox[3]-trim_layer_bbox[1])

    # -- test 5: no trim with oob trim
    args["trim_to_size"]    = True
    args["trim_layers"]     = False
    args["trim_to_visible"] = False

    args       = get_export_args(**args)
    expimg      = ExportableImg(layer, layer_name, "psd_test2",**args)
    image       = layer_to_img(expimg.image,**expimg.get_args())
    
    # ✅image size is NOT layer size
    assert layer.size != image.size #type:ignore
    # ✅image size is NOT trimmed layer size
    assert image.size != trim_layer_size #type:ignore
    # ✅ image size IS canvas size
    assert image.size == args["canvas_size"] #type:ignore
    # ✅image size is NOT full visible psd size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    
def test_layer_to_img_no_trim_no_trim_visible():
    # test that when we do trim each layer, a layer that's bigger than canvas size gets trimmed to canvas size
    # use psd_test2.psd
    #Init
    opened_psd = open_psd("psd_test2.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)
    

    # Use a suitable layer
    layer_name  = "Layer 2"
    layer       = psd.find(layer_name)
    trim_layer_bbox = trim_oob_bbox(layer.bbox,list(psd.size) )
    trim_layer_size =  (trim_layer_bbox[2]-trim_layer_bbox[0],trim_layer_bbox[3]-trim_layer_bbox[1])

    # -- test 6: no trim WITHOUT oob trim
    args["trim_to_size"]    = False
    args["trim_layers"]     = False
    args["trim_to_visible"] = False

    args       = get_export_args(**args)
    expimg      = ExportableImg(layer, layer_name, "psd_test2",**args)
    image       = layer_to_img(expimg.image,**expimg.get_args())

    # image size is not layer size
    assert layer.size != image.size #type:ignore
    # ✅image size is NOT trimmed layer size
    assert image.size != trim_layer_size #type:ignore
    # ✅image size is canvas size??
    assert image.size == args["canvas_size"] #type:ignore
    # ✅image size is not full visible psd size...??
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    
def test_layer_to_img_crop_to_layer():
    #Init
    opened_psd = open_psd("psd_test.psd")
    psd        = opened_psd["psd"]
    args       = app_kwargs_init(opened_psd)

    # set crop layer 
    crop_layer = psd.find("Layer2")
    args["crop_layer"] = crop_layer

    # Update args
    args       = get_export_args(**args)

    # Use a suitable layer
    layer_name  = "base"
    expimg      = ExportableImg(psd.find(layer_name), layer_name, "psd_test",**args)
    image       = layer_to_img(expimg.image,**expimg.get_args())

    # Make sure it matches the crop_layer's bbox
    assert image.size == crop_layer.size #type:ignore
    # Not the PSD visible size
    assert image.size != (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1]) #type:ignore
    # It's not the same as the layer size
    assert image.size != psd.find("base").size #type:ignore
    # It's not the same as canvas size
    assert image.size != args["canvas_size"] #type:ignore

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
    assert image.size != psd.find("base").size #type:ignore
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
