from psd_funcs import *
from project import * #type:ignore

def main():
    #testing_trim_oob()
    testing_crop_to_mask()


def testing_crop_to_mask():
    print("testing crop to mask")
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

    mask_size = psd.find(layer_name).mask.size
    mask_bbox = psd.find(layer_name).mask.bbox
    psd_vis_size = (psd.bbox[2]-psd.bbox[0],psd.bbox[3]-psd.bbox[1])
    print("mask bbox:", mask_bbox)

    # Make sure it matches the mask's size
    print("img size:",image.size, "should be:", mask_size) #type:ignore
    print("canvas size:",args["canvas_size"],"psd visible size: ", psd_vis_size, "layer size:", psd.find(layer_name).size)
    
    
def testing_trim_oob():
    opened_psd   = open_psd("psd_test2.psd")
    args         = app_kwargs_init(opened_psd)
    psd          = opened_psd["psd"]


    #print("layer's bbox:", layer.bbox, "canvas bbox:", canvas_bbox, "psd bbox", psd.bbox)
    #print("layer corrected bbox:", corrected_psd_bbox , "psd corrected bbox:", trim_oob_bbox(psd,args["canvas_size"]))
    #print("corrected bbox:",trim_outofcanvas_bbox(layer,list(args["canvas_size"]) ))
    args["trim_to_size"]    = True
    args["trim_layers"]     = False
    args["trim_to_visible"] = False

    args = get_export_args(**args)

    # find layer that is to big
    layer       = psd.find("Layer 2")
    canvas_bbox = tuple( [0,0] + list(args["canvas_size"]))
    corrected_psd_bbox = trim_oob_bbox(psd.bbox,args["canvas_size"])
    target_size = args["canvas_size"]#(corrected_psd_bbox[2]-corrected_psd_bbox[0],corrected_psd_bbox[3]-corrected_psd_bbox[1])

    expimg   = ExportableImg(layer, "Layer 2", "psd_test2",**args)
    image    = layer_to_img(expimg.image,**expimg.get_args())
    print("bbox in args:",args["bbox"], "(should be",args["canvas_size"],")")
    print("image size:", image.size, "(should be",target_size,") layer size is:",layer.size) #type:ignore


if __name__ == "__main__":
    main()
