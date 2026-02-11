from psd_tools import PSDImage
from psd_tools.api.layers import Layer, Group
from pathlib import Path
from PIL import Image, ImageChops
import re


#--------------------------
#  PSD Processing

class ExportableImg():
    """
    Docstring for ExportableImg
    
    :var export_args: Description
    :vartype export_args: Any
    :var image: Description
    :vartype image: Any
    """
    def __init__(self, image: Layer | PSDImage, name: str, path: str, ext= ".png", **kwargs):
        self.image   = image
        self.name    = name
        self.path    = path
        self.ext     = ext
        self.visible = image.visible
        self.exportargs  = []
        for arg in kwargs:
            setattr(self,arg,kwargs[arg])
            self.exportargs.append(arg)

    def get_bbox(self):
        """gets bbox if not specified"""
        bbox = getattr(self,"bbox", None)
        return bbox if bbox else self.image.bbox
    
    def get_savepath(self):
        """returns filepath"""
        return self.path+"/"+self.name+self.ext

# def get_ignore(self):
#     """returns if the file should be ignored or not"""
#     # the extra ignore conditions are dealt with on process_psd itself, before we get to this point.

#     if not self.visible and getattr(self,"ignore_invisible",True):
#         return True
    
#     if isinstance(self.image, Layer) and self.image.clipping:
#         return True

#     return False
    
    def get_args(self)-> dict:
        """returns a dictionary with relevant export kwargs"""
        args = {k:getattr(self,k) for k in self.exportargs}
        args["bbox"] = self.get_bbox()
        return args

    def save(self) -> bool|str:
        """Saves the image to the path with the extension given, if it's not ignored"""
        
        # if this should be ignored, move on.
        #if self.get_ignore():
        #    return True
        
        # get export args
        export_args = self.get_args()

        # if this is a layer, make sure the layer is visible.
        if not isinstance(self.image, PSDImage):
            self.image.visible = True #type:ignore
        
        # convert to a pil image, using the export args
        image = layer_to_img(self.image, **export_args)

        # if the image succeeded in being created, process and save
        if image:

            # Scale it if we're doing that
            if export_args["scale"] != 1.0:
                
                if export_args["scale"] > 5.0:
                    raise ValueError("Sorry, scale is way too big! (how did we get here???)")
                    
                #if we're keeping aspect ratio:
                if export_args["keep_aspect_ratio"]:
                    new_size = tuple(int(i*export_args["scale"]) for i in image.size)
                
                #if not..
                else:
                    og_size = export_args["canvas_size"]
                    w_scale = get_width_scale(og_size,int(export_args["width"]))
                    h_scale = get_height_scale(og_size,int(export_args["height"]))
                    
                    new_size = tuple([int(round(w_scale*image.size[0])),int(round(h_scale*image.size[1]))])
                
                
                image = image.resize(new_size, Image.Resampling.LANCZOS) #type: ignore

            # finally, save it
            image.save(self.get_savepath())

        # return visibility to what it was originally
        if not isinstance(self.image, PSDImage) and not self.visible:
            self.image.visible = self.visible # type:ignore

        # check if the saved image exists, return True
        if check_image_exists(self.get_savepath()):
            return True
    
        return f"Failed to export {self.name}"

def process_psd(psd:PSDImage|Group, name, path, **kwargs) -> bool | str:
    """Processes a PSD (and layer groups recursively), by going through all the layers/groups and exporting them"""

    selected        = kwargs.get("selected", [])
    flatten         = kwargs.get("flatten", [])
    selected_action = kwargs.get("selected_action",None)
    ignore_invisible= kwargs.get("ignore_invisible",True)

    # if we're flattening, flatten the psd
    if kwargs.get("flat", False) or "*" in flatten: 
        return ExportableImg(psd,name,path,**kwargs).save()
    
    # otherwise, iterate over layers
    for layer in psd:
        # get what we should do with this layer
        layer_action = what_do(layer,selected,flatten,selected_action)

        # if it should be ignored, pass
        if any([
            not layer.visible and ignore_invisible,
            layer.clipping,
            layer_action == "ignore"
            ]):
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

            # create a new folder
            new_path     = path+"/"+group_name
            Path(new_path).mkdir(parents=True, exist_ok=True)

            # Check if this group has a mask enabled
            mask = layer.mask if layer.has_mask() and not layer.mask.disabled else None #type:ignore

            # if we have a mask, save it to apply it to its children
            if mask:
                group_kwargs = process_mask(mask,group_kwargs)

            # if we are exporting the whole group, add "*" to selected
            if layer_action == "export":
                group_kwargs["selected"].append("*")

            # Process the group
            process_psd(layer, group_name, new_path, **group_kwargs) #type:ignore

    return True

#---------

def process_mask(mask,group_kwargs:dict)->dict:
    """Helper of process_psd to process the mask of a group and save it in a dict to pass it down to its descendants"""
    
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

def what_do(layer:Layer|None, selected:list=[], flatten:list=[], what:str|None="export")->str:
    """Determines what to do with a layer during processing, given a list of selected items, what to do with those selected items, and a list of layers to flatten."""
    
    if not layer:
        return "ignore"
    
    if not selected:
        what = None

    layer_is_selected = is_selected(layer, selected)
    
    if what == "ignore" and layer_is_selected:
        return "ignore"
        
    if layer.is_group():
        if is_selected(layer,flatten) and not all([layer_is_selected, what == "ignore"]):
            return "save"
        
        elif what == "export" and layer_is_selected:
            return "export"
        
        return "pass"
    
    else:
        if what =="export" and not layer_is_selected:
            return "ignore"
        return "save"

def is_selected(layer:Layer|None, selected:list)->bool:
    """Return if a layer is selected based off whatever is in the selected list (names, expressions and (layer,parent) tuples)"""
    # abort if no layer given
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
    """converts a list of wildcard expressions into a regex string"""
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

def dummy_process(psd:PSDImage|Layer, selected:list=[], what:str|None=None, flatten:list=[]) -> list:
    """Temp function to test logic before applying it to process_psd"""
    filtered = []
    
    for layer in psd: #type:ignore
        layer_action = what_do(layer,selected,flatten,what)
        layer_append = (layer.name, layer.parent.name)

        if layer_action == "save":
            filtered.append(layer_append)
        
        elif layer_action == "ignore":
            pass

        elif layer.is_group(): 
            if layer_action == "pass":
                filtered = filtered + dummy_process(layer,selected,what,flatten)
    
            elif layer_action=="export":
                filtered = filtered + dummy_process(layer,["*"],what,flatten)

    return filtered

def get_all_layernames(psd:PSDImage)->list:
    """returns a list of *all* of the layer names in a file with their parents"""
    layers = []
    for layer in psd.descendants():
        layers.append((layer.name,layer.parent.name)) #type: ignore
    return layers

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
    bbox         = kwargs.get("bbox", layer.bbox) # bounding box to crop the Layer. Default is the layer's own bbox 
    alpha        = kwargs.get("alpha", None) # alpha mask image. Only exists if layer is inside a group that has a mask.
    trim_to_mask = kwargs.get("trim_to_mask", False) # if we're cropping layers to their mask's bbox.
    canvas_size  = kwargs.get("canvas_size",(bbox[2],bbox[3]))
    
    # If we got a PSDImage, flatten it and return.
    if isinstance(layer,PSDImage):

        # if we're trimming, bbox is psd visible layers bbox, otherwise is canvas size.
        bbox = layer.bbox if trim_layers else tuple([0,0] + list(layer.size)) # don't use canvas_size unless we're cropping!

        return layer.composite(force = True, viewport=bbox) #type: ignore
        
    
    if not alpha:
        
        # If this layer has a mask and we're trimming to mask, make the mask's bbox the layer's bbox
        if all([trim_to_mask, layer.has_mask() and not layer.mask.disabled]): #type: ignore
            bbox = layer.mask.bbox # type: ignore
        
        # Return the composited layer.
        return layer.composite(viewport=bbox)
        
    # composites with alpha
    image = composite_alpha(layer,alpha,canvas_size)

    # Trim the image if we're not trimming to mask and we don't have trimming disabled.
    if not trim_to_mask and trim_layers:
        bbox  = image.getbbox()  # type:ignore

    # return cropped image!   
    return image.crop(bbox) # type:ignore

def create_alpha(mask, canvas_size) -> Image.Image|None:
    """converts a layer mask to b/w image to save on alpha channel"""

    og_mask  = mask.topil().convert("L") #type: ignore
    new_mask = Image.new("RGB", canvas_size , color=(0,0,0)).convert("L")

    Image.Image.paste(new_mask,og_mask,(mask.bbox[0],mask.bbox[1]))

    return new_mask

def composite_alpha(layer,alpha,canvas_size) -> Image.Image|None: 
    """Composites layer and applies an alpha mask image to it"""

    # Alpha processing: 
    viewport    = tuple([0,0] + list(canvas_size))
    image       = layer.composite(force = True, viewport = viewport) #type: ignore

    # split image into channels to get the layer's mask/alpha channel
    *_, og_alpha = image.split() #type:ignore

    # combine layer's mask with our pre-saved alpha
    new_alpha    = ImageChops.multiply(alpha, og_alpha)

    # replace image's alpha with our new combined alpha
    image.putalpha(new_alpha) #type:ignore

    return image

# resize auxs for GUI and Save ----  

def get_height_scale(og_size,new_height)->float:
    """returns height scale"""
    return get_scale(og_size,height=new_height)

def get_width_scale(og_size,new_width)->float:
    """returns width scale"""
    return get_scale(og_size,width=new_width)
     
def get_scale(size:tuple[int,int], width=None, height=None)-> float:
    """returns a float that corresponds what % of the og width/heigh is the given width/height"""
    ogw, ogh = size
    if width:
        return width/ogw
    elif height:
        return height/ogh
    return 1.0

def size_convert(size:tuple[int,int],input:tuple[int,int],kind:str="%") -> tuple[int,int]:
    """Convert from % to px or viceversa"""
    w, h     = input

    # Converting to pixels, meaning I must have been given px
    if kind == "px":
        nw = get_resize(size, width = w, convert = True)
        nh = get_resize(size, height= h, convert = True)

    # converting to %, so i assume I was given px
    else:
        nw = get_resize(size, width=w, kind="px", convert=True)
        nh = get_resize(size, height=h, kind="px", convert=True)

    return (nw,nh)

def get_resize(size:tuple[int,int], kind:str="%", **kwargs) -> int:
    """Returns correct size. Needs h or w, otherwise raises an error."""
    ogw, ogh = size
    ratio    = ogw/ogh
    w,h      = kwargs.get("width", None),kwargs.get("height", None)
    convert  = kwargs.get("convert",False)

    if w == None and h == None:
        raise ValueError("No value provided for neither W nor H")
    # What are we trying to do?

    # We're converting from % to px and viceversa
    if convert:
        # if we're given %, we need to convert to px
        if kind == "%":
            if w:
                return round(ogw*w/100)
            elif h:
                return round(ogh*h/100)

        # if we're given px, convert to %
        else:
            if w:
                return w/ogw*100
            elif h:
                return h/ogh*100
        
    # if we're not converting, we want the value not provided. Only needed for keepratio.
    else:
        # %h = %w, so return the same value given.
        if kind == "%":
            return w if w else h #type:ignore
        # here we need to calculate the value not given by using the ratio
        else:
            # if given width, return height
            if w:
                return round(w/ratio)
            # if given height, return width
            elif h:
                return round(ratio*h)

    # if we're not converting and not keeping ratio, error.
    return -1

#--------------------
# GUI Integration

def get_psd_thumbnail(psd):
    """returns a thumbnail image for a psd"""
    thumb = psd.thumbnail()
    
    if not thumb:
        image = psd.composite(apply_icc=False)
        w, h = image.size
        new_h = 120
        new_w = int(1/(h/w) * new_h)
        thumb = image.resize((new_w, new_h))

    return thumb

def get_psd_dir(filename):
    """matches a string and returns a match"""
    match = re.match(r"(.*/).*\.psd",filename)
    if match:
        return match.group(1)
    return '/'

#----------------------------------
# Tree

def get_repr(psd:PSDImage)->str:
    """PSD Layer structure as a string"""
    text = ""

    if not psd:
        return text
    
    text = text+get_layer_repr(psd) # type: ignore

    return text

def get_layer_repr(layers:list[Layer], level=0)->str:
    """returns Layer name if layer is Layer, it iterates over itself appending names if it's a group."""
    
    text = ""
    layer_kinds ={"group": "📂", "pixel": "🎨", "type": "✒️", "shape": "🔷"}

    
    for layer in layers:
        layer_name = layer_kinds.get(layer.kind,"📄")+" "+layer.name

        # invisible layer has an icon
        if not layer.visible:
            layer_name = "🫥"+layer_name
        
        if layer.has_mask():
            layer_name = layer_name+" "+"⏺"

        if layer.clipping:
            layer_name = "↷"+layer_name

        if not layer.is_group():
            text = "   "*level + layer_name+"\n"+text

        else:
            text = "   "*level + layer_name+"\n"+get_layer_repr(layer, level = level+1)+text #type: ignore
    
    return text

#---------------------------
# PSD opening on GUI

def open_psd(filename:str) -> dict:
    """
    This function opens a PSD file from a path str and returns a dict with a PSDImage object and its name (filename.psd).
    If it fails, it returns an empty dict, signaling its failure.

    Parameters:
        filename (str) : A path str to open a PSD file.
    
    Returns:
        dict: a dictionary containing the PSD file itself and the name of the file.
    """
    psd_dict = dict()
    try:
        psd_dict["psd"] = PSDImage.open(filename)
        
    except:
        return {}
    
    psd_dict["psd_name"] = get_psd_filename_from_path(filename)
    psd_dict["psd_size"] = psd_dict["psd"].size

    return psd_dict

def get_psd_filename_from_path(filename:str) -> str:
    """ Given a string that's a path to a file, this function returns a string with the name of the file (extension included)"""
    match = re.search(r"(?:.*\/)?(.*.psd)",filename)
    if match:
        return match.group(1)
    return ""

def get_export_args(**kwargs) -> dict:
    """Given a dict, it initializes all kwargs for process.psd"""
    
    # default arg values
    default = {
        "extension"         : ".png",
        "ignore_invisible"  : True,
        "trim_layers"       : True,
        "trim_to_mask"      : False,
        "trim_to_visible"   : False,
        "scale"             : 1.0,
        "bbox"              : None,
        "selected"          : [],
        "selected_action"   : None,
        "flatten"           : [],
        "keep_aspect_ratio" : True,
        "kind"              : "%",
        "height"            : 0,
        "width"             : 0
    }

    # make a new dict by replacing default values with kwargs we got
    args = {k:kwargs.get(k,default[k]) for k in default}

    # record the canvas size for future reference
    args["canvas_size"] = kwargs["file"]["psd_size"] #type: ignore
    
    # Define the bbox if we're not trimming empty pixels
    if not args["trim_layers"]:

        # if we want to trim to the visible layers of the psd, get the psd's bbox
        if args["trim_to_visible"]:
            args["bbox"] = kwargs["file"]["psd"].bbox #type: ignore
        
        # otherwise, bbox is document size.
        else:
            args["bbox"] = tuple([0,0] + list(args["canvas_size"])) #type:ignore
            
    return args

