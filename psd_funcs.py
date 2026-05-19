from psd_tools import PSDImage
from psd_tools.api.layers import Layer, Group
from pathlib import Path
from PIL import Image, ImageChops
import re


#--------------------------
#  PSD Processing

class ExportableImg():
    """
    Class that contains a PSDImage, Layer or Group to be exported as an image file.

    Attributes
    ----------
    image : Layer | PSDImage
        the source of the image that will be saved.
    name : str
        name that will be used to save the file
    path : str
        path where ther image will be saved
    ext  : str
        extension the image file will be saved in. defauls is '.png'
    visible : bool
        the image's visibility attribute 
    exportargs : list
        a list of attributes that will be taken into consideration when saving the image


    Methods
    -------
    get_bbox():
        returns the object's bbox (bounding box : (left, top, right, bottom) coordinates).

    get_savepath():
        returns the filepath to save the image.

    get_args():
        returns a dictionary with relevant kwargs for exporting that were passed to the object at the moment of creation.

    save():
        Saves the image to disk.
    
    """

    def __init__(self, image: Layer | PSDImage, name: str, path: str, **kwargs) -> None:
        """
        Constructs the attributes for the ExportableImage object.

        Parameters
        ----------
            image : Layer | PSDImage
                the source of the image to be saved
            name : str
                the name to use when saving the image
            path : str
                path where ther image will be saved
            **kwargs: Any
                other named parameters that will be saved as attributes

        Raises
        ------
            ValueError: No Layer provided
        """

        self.image   = image
        if not image:
            raise ValueError("No Layer provided")
        self.name    = name
        self.path    = path
        self.ext     = kwargs.get("extension",".png")
        self.visible = image.visible
        self.exportargs  = []
        for arg in kwargs:
            setattr(self,arg,kwargs[arg])
            self.exportargs.append(arg)

    def get_bbox(self) -> tuple[int,int,int,int]:
        """
        Returns the object's bbox (bounding box : (left, top, right, bottom) coordinates).

        Returns
        -------
        tuple[int,int,int,int]
        """
        bbox = getattr(self,"bbox", None)
        return bbox if bbox else self.image.bbox
    
    def get_savepath(self) -> str:
        """
        Returns the filepath to save the image.

        Returns
        -------
        str
        """
        return self.path+"/"+self.name+self.ext
    
    def get_args(self)-> dict:
        """
        Returns a dictionary with relevant kwargs for exporting that were passed to the object at the moment of creation.

        Returns
        -------
        dict
        """
        # create the dict from self.exportargs list
        args = {k:getattr(self,k) for k in self.exportargs}
        # make sure to have the correct bbox
        args["bbox"] = self.get_bbox()

        return args

    def save(self) -> bool|str:
        """
        Saves the image to disk.
        
        Returns
        -------
        bool | str (upon failure)
        """
        
        # get exporting args
        export_args = self.get_args()

        # if this is a layer, make sure the layer is visible. Do nothing if it's the psd file itself.
        if not isinstance(self.image, PSDImage):
            self.image.visible = True #type:ignore
        
        # convert the layer to a pil image, using the export args
        image = layer_to_img(self.image, **export_args)

        # if the image succeeded in being created, process and save
        if image:

            # Resize it if we're doing that
            if export_args["scale"] != 1.0:
                
                # abort if scale is too big
                if export_args["scale"] > 5.0:
                    raise ValueError("Sorry, scale is way too big! (how did we get here???)")
                    
                # if we're keeping aspect ratio, get new size from the "scale" argument. 
                if export_args["keep_aspect_ratio"]:
                    new_size = tuple(int(i*export_args["scale"]) for i in image.size)
                
                # Otherwise, caculate new size based off the "width" and "height" arguments.
                else:
                    og_size = export_args["canvas_size"]
                    w_scale = get_width_scale(og_size,int(export_args["width"]))
                    h_scale = get_height_scale(og_size,int(export_args["height"]))
                    
                    new_size = tuple([int(round(w_scale*image.size[0])),int(round(h_scale*image.size[1]))])
                
                # Resize the image to its new size
                image = image.resize(new_size, Image.Resampling.LANCZOS) #type: ignore

            # Create the container folder if it doesn't exist
            Path(self.path).mkdir(parents=True, exist_ok=True) 
            
            # finally, save it
            image.save(self.get_savepath())

        # return visibility to what it was originally
        if not isinstance(self.image, PSDImage) and not self.visible:
            self.image.visible = self.visible # type:ignore

        # At last, check if the saving of the image was successful.
        if check_image_exists(self.get_savepath()):
            return True

        # if the image failed, return a failure message.
        return f"Failed to export {self.name}"

def process_psd(psd:PSDImage|Group, name, path, **kwargs) -> bool | str:
    """
    Processes a PSD (and layer groups recursively), by going through all the layers/groups and exporting them based on parameters given.
        
        Parameters:
            psd (PSDImage|Group): A PSDImage or a Group from a PSD file that contains layers.
            name (str): name of the file or group.
            path (str): path where the image(s) should be saved 
            **kwargs: other named parameters

        Returns:
            result (bool | str): either True if the process goes without issues, or a string with a failure message.
    """

    selected        = kwargs.get("selected", [])
    flatten         = kwargs.get("flatten", [])
    selected_action = kwargs.get("selected_action",None)
    flatten_action  = kwargs.get("flatten_action",None)
    ignore_invisible= kwargs.get("ignore_invisible",True)

    # if we're dealing with the psd, create the main folder first
    if isinstance(psd,PSDImage):
        Path(path).mkdir(parents=True, exist_ok=True)

    # if we're flattening, flatten the psd
    if kwargs.get("flat", False) or "*" in flatten: 
        return ExportableImg(psd,name,path,**kwargs).save()

    # otherwise, iterate over layers
    for layer in psd:

        # if it's the crop layer (if any), skip it
        if layer == kwargs.get("crop_layer"):
            pass

        # get what we should do with this layer
        layer_action = what_do(layer,selected,flatten,selected_action, flatten_action, ignore_invisible=ignore_invisible)

        # if it should be ignored, pass
        if layer_action == "ignore":
            pass

        # if layer should be saved, save it
        elif layer_action == "save":
            result = ExportableImg(layer,layer.name,path,**kwargs).save()

            #if an error ocurred while saving, return it
            if result != True:
                return result

        # Otherwise, go into the thing because it has to be a group.
        else:
            # get the name
            group_name   = layer.name

            # make new kwargs to not contaminate the og
            group_kwargs = dict(kwargs)

            # save the group as a new path to pass down
            new_path     = path+"/"+group_name

            # Check if this group has a mask enabled
            mask = layer.mask if layer.has_mask() and not layer.mask.disabled else None #type:ignore

            # if we have a mask and we're applying masks to children, save it in the group kwargs to apply it to its children
            if mask and group_kwargs["apply_group_mask"]:
                group_kwargs = process_mask(mask,group_kwargs)

            # if we are exporting the whole group, add "*" to selected so it treats everything as selected,
            if layer_action == "export":
                group_kwargs["selected"]=["*"]

            # Process the group
            process_psd(layer, group_name, new_path, **group_kwargs) #type:ignore

    return True

#---------

def process_mask(mask,group_kwargs:dict)->dict:
    """Helper of process_psd() to process the mask of a group and save it in a dict, to pass it down to its descendants."""
    
    if not mask:
        return group_kwargs
    
    # if we're trimming to mask, assign the mask bbox to the group's export bbox. 
    # This overrides canvas size and layer trimming.
    if group_kwargs.get("trim_to_mask",False):
        group_kwargs["bbox"] = mask.bbox # type: ignore

    # Convert the mask to an alpha b/w image and store it
    group_kwargs["alpha"] = create_alpha(mask, group_kwargs.get("canvas_size", (mask.bbox[2],mask.bbox[3]))) #type:ignore
    
    # if we don't have a bbox, save the bbox as the mask bbox. We'll trim later when exporting.
    if not group_kwargs.get("bbox", None):
        group_kwargs["bbox"] = mask.bbox # type: ignore

    return group_kwargs

def what_do(layer:Layer|None, selected:list=[], flatten:list=[], selected_action:str|None="export", flatten_action:str|None="flatten",ignore_invisible=True, ignore_clippings=True)->str:
    """Determines what to do with a layer during processing, given a list of selected items, what to do with those selected items, and a list of layers to flatten."""
    
    # First of all, if layer is empty, not a layer, or an adjustment layer without pixels, ignore it right away.
    if not layer or layer.kind not in ["group","pixel","type","shape","solidcolorfill","patternfill","gradientfill"]:
        return "ignore"
    
    # First, check if the layer qualifies as selected.
    layer_is_selected = is_selected(layer, selected)
    
    # Now, check if we have selection or flatten dierectives. If not, then set their respective actions to None.
    selected_action = selected_action if selected else None
    flatten_action  = flatten_action if flatten else None
    
    # With that, ignore the layer if fits our ignoring criteria.
    if any([
        selected_action == "ignore" and layer_is_selected,
        ignore_invisible and not layer.visible,
        ignore_clippings and layer.clipping
        ]):
        return "ignore"
        
    # If our layer is a single layer that wasn't already ignored
    if not layer.is_group():
        # if it's NOT selected and we're exporting only the selected, ignore it.
        if selected_action =="export" and not layer_is_selected:
            return "ignore"
        # Otherwise, save it as an image.
        return "save"
        
    # if our layer is a group instead
    else:
        # if it's flatten-selected
        if is_selected(layer,flatten):
            # if we're flattening everything but the selected, pass
            if flatten_action == "ignore":
                return "pass"
            # otherwise, flatten it and save it.
            else:
                return "save"
        
        # if it's NOT selected and flatten_action is 'ignore' (flattening the unselected), flatten it
        elif flatten_action == "ignore":
            return "save"

        # if we're exporting the selected and it's selected, export its contents
        elif selected_action == "export" and layer_is_selected:
            return "export"
        
        # if nothing applies, pass
        return "pass"
        
def is_selected(layer:Layer|None, selected:list)->bool:
    """Return if a layer is selected based off whatever is in the selected list (names, expressions and (layer,parent) tuples)"""
    # abort if no layer or list given
    if not layer or not selected:
        return False
    
    # if the name is in the list
    if any([layer.name in selected, 
            (layer.name,layer.parent.name) in selected ]): #type:ignore
        return True
    
    patterns = [i for i in selected if "*" in i]
    if patterns:
        match = re.search(get_regex(patterns), layer.name, flags=re.IGNORECASE)
        
        if match:
            return True

    return False
    
def get_regex(expressions:list)->str:
    """converts a list of wildcard expressions into a usable regex string"""
    rex=[]
    for i in expressions:
        
        # Prefix, ie: "layer*""
        if i.endswith("*") and not i.startswith("*"):
            i = "^"+i[:-1]

        # Suffix, ie: "*layer"
        elif not i.endswith("*") and i.startswith("*"):            
            i = i[1:]+"$"
        
        # Contains word, #ie: "*layer*"
        elif i.endswith("*") and i.startswith("*"):
            i = i.replace("*","")

        # Exact name*, ie: "layer1"
        else:
            i = "^"+i+"$"

        # Expressions with wildcard(s) in the middle, ie: "char_*_eye"
        # Also catches all expressions that have * in the middle regardless if they have other * at the end or the beginning
        #  like "*a*b", "a*b*" and "*a*b*"
        if "*" in i:
            i = i.replace("*",".*")

        # append the regex conversion to list      
        rex.append(i)
        
    # join all the regexes separated by "|"" and put the result inside "()"
    return r"(" + "|".join(rex) + ")"

#----------------------------------------------------------------
# PSD Processing - aux

def check_image_exists(filepath)->bool:
    """Checks if an image file exists"""
    if Path(filepath).is_file():
        return True
    return False

#----------------------------
# Image Creation

def layer_to_img(layer:Layer|PSDImage, **kwargs) -> Image.Image | None:
    """Composites a Layer/PSDImage and returns an image. Returns None if the image creation fails"""   
    
    # Retrieve some pertinent arguments
    trim_layers  = kwargs.get("trim_layers", True) # Are we trimming pixels?
    trim_to_size = kwargs.get("trim_to_size", True) # Are we cropping stuff outside of canvas?
    bbox         = kwargs.get("bbox", layer.bbox) # bounding box to crop the Layer. Default is the layer's own bbox 
    alpha        = kwargs.get("alpha", None) # alpha mask image. Only exists if layer is inside a group that has a mask.
    trim_to_mask = kwargs.get("trim_to_mask", False) # if we're cropping layers to their mask's bbox.
    canvas_size  = kwargs.get("canvas_size",(bbox[2],bbox[3]))
    crop_layer   = kwargs.get("crop_layer",None) #do we have a crop layer?
    crop         = kwargs.get("crop",False) #are we cropping with bbox?

    crop = any([crop_layer, crop]) 

    # record layer and parent visibility and make them all visible
    if not isinstance(layer,PSDImage):
        visible = layer.visible
        parent_visible = layer.parent.visible #type:ignore
        grandparent_visible = None if layer.parent.name == "Root" else layer.parent.parent.visible#type:ignore
        layer.visible = True
        if layer.parent.name != "Root": #type:ignore
            layer.parent.visible = True #type:ignore
            if layer.parent.parent.name != "Root": #type:ignore
                layer.parent.parent.visible = True #type:ignore
    
    # if our layer is a shape, the bbox is the vector_mask's bbox, not the layer's bbox
    if layer.kind == "shape":
        bbox = layer.mask.bbox if bbox == layer.bbox else bbox#type:ignore

    # if we're cropping, set the bbox
    if crop:
        bbox = crop_layer.bbox if crop_layer else bbox

    # If we got a PSDImage, flatten it and return.
    if isinstance(layer,PSDImage) or not alpha:

        # If this layer has a mask and we're trimming to mask, make the mask's bbox the layer's bbox
        if not isinstance(layer,PSDImage) and all([trim_to_mask, layer.has_mask() and not layer.mask.disabled, not crop]): #type: ignore
            bbox = layer.mask.bbox # type: ignore

        # if we're cropping, keep the bbox we already defined
        if crop:
            bbox = bbox
        # if we're trimming, bbox is psd visible layers bbox, otherwise is canvas size.
        elif trim_to_size:
            bbox = trim_oob_bbox(bbox, canvas_size) if trim_layers else bbox
        elif trim_layers:
            bbox = layer.bbox if layer.kind != "shape" else layer.mask.bbox #type:ignore
        
        if layer.kind == "shape":
            print(layer.name, "is shape. layer bbox:", layer.bbox, "saved bbox:", bbox, "mask bbox:", layer.mask.bbox) #type:ignore
        else:
            print(layer.name, "is not shape. layer bbox:", layer.bbox, "saved bbox:", bbox)
            
        image = layer.composite(force = True, viewport=bbox) #type: ignore
        
        
        # return visibility to layers and parents before returning
        if not isinstance(layer,PSDImage):
            layer.visible = visible #type:ignore
            if layer.parent.name != "Root": #type:ignore
                layer.parent.visible = parent_visible #type:ignore
                if layer.parent.parent.name != "Root": #type:ignore
                    layer.parent.parent.visible = grandparent_visible #type:ignore

        #return image
        return image.crop(image.getbbox()) if trim_layers and image else image #type: ignore

    # composites with alpha
   
    image = composite_alpha(layer,alpha,canvas_size)

    # Trim the image if we're not trimming to mask and we don't have trimming disabled.
    if not trim_to_mask and trim_layers and not crop:
        bbox  = image.getbbox()  # type:ignore

    # return cropped image!   
    image = image.crop(bbox)#type:ignore
    # return visibility to layers and parents before returning
    if not isinstance(layer,PSDImage):
        layer.visible = visible #type:ignore
        if layer.parent.name != "Root": #type:ignore
            layer.parent.visible = parent_visible #type:ignore
            if layer.parent.parent.name != "Root": #type:ignore
                layer.parent.parent.visible = grandparent_visible #type:ignore
    return image # type:ignore

def create_alpha(mask, canvas_size) -> Image.Image|None:
    """Converts a layer mask to b/w image of the canvas size provided"""

    if not mask:
        return None
    
    og_mask  = mask.topil().convert("L") #type: ignore
    new_mask = Image.new("RGB", canvas_size , color=(0,0,0)).convert("L")

    Image.Image.paste(new_mask,og_mask,(mask.bbox[0],mask.bbox[1]))

    return new_mask

def composite_alpha(layer:Layer|Group|None, alpha:Image.Image|None, canvas_size:tuple) -> Image.Image|None: 
    """Composites a layer and applies a b/w image to its alpha channel"""

    if any([not layer, not alpha]):
        return None
    
    # Composite layer to the canvas size: 
    image = layer.composite(force = True, viewport = tuple([0,0] + list(canvas_size))) #type: ignore

    # split image into channels to get the layer's mask/alpha channel
    *_, og_alpha = image.split() #type:ignore

    # combine layer's mask/alpha with our pre-saved alpha
    new_alpha    = ImageChops.multiply(alpha, og_alpha) #type:ignore

    # replace image's alpha with our new combined alpha
    image.putalpha(new_alpha) #type:ignore

    # return the image
    return image

# resize auxs used by ExportableImg.save() and reused by the App in project.py ----  

def get_height_scale(og_size,new_height)->float:
    """returns height scale"""
    return get_scale(og_size,height=new_height)

def get_width_scale(og_size,new_width)->float:
    """returns width scale"""
    return get_scale(og_size,width=new_width)
     
def get_scale(size:tuple[int,int], width=None, height=None)-> float:
    """returns a float that corresponds to what % of the og width/heigh is the given width/height"""
    ogw, ogh = size
    if width:
        return width/ogw
    elif height:
        return height/ogh
    return 1.0

# -----
# Layer bbox vs canvas bbox
def trim_oob_bbox(layer_bbox,canvas_size) -> tuple[int, int, int, int]:
    """returns a corrected bbox if the layer's bbox is out of bounds of the canvas size"""
    canvas_bbox = (0,0,canvas_size[0],canvas_size[1])
    layer_bbox  = layer_bbox if not isinstance(layer_bbox,(Layer, PSDImage)) else layer_bbox.bbox

    # if they're the same, return the layer's bbox
    if canvas_bbox == layer_bbox:
        return layer_bbox
    
    # otherwise, adjust coords one by one
    else:
        bbox = list(canvas_bbox)
        # top left
        bbox[0] = canvas_bbox[0] if layer_bbox[0] <= canvas_bbox[0] else layer_bbox[0]
        bbox[1] = canvas_bbox[1] if layer_bbox[1] <= canvas_bbox[1] else layer_bbox[1]
        # bottom right
        bbox[2] = canvas_bbox[2] if layer_bbox[2] >= canvas_bbox[2] else layer_bbox[2]
        bbox[3] = canvas_bbox[3] if layer_bbox[3] >= canvas_bbox[3] else layer_bbox[3]
        return tuple(bbox) #type:ignore
     
