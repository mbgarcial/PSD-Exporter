

from psd_funcs import *
import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog as fd #This is for opening files
import tkinter.scrolledtext as scrolledtext
from PIL import ImageTk
from functools import partial


# CREDITS:
# How to add an image in tkinter: https://www.geeksforgeeks.org/python/how-to-add-an-image-in-tkinter/
# Save pil image with saveasfile tkinter: https://www.daniweb.com/programming/software-development/threads/520677/how-to-save-the-edited-photo-tkinter-as-jpg-with-asksaveasfilename#:~:text=Dani%20AI,image%20as...'%2C
# tkinter how to trace (GeeksforGeeks), how to get the focused widget https://stackoverflow.com/questions/41291779/how-to-get-widget-name-in-event


class App:
    """Configures and adds widgets to a tk window. Also handles functions that are passed to said widgets."""
    def __init__(self, master, geometry = "500x300+400+300"):
        # Master is the TK window we'll be applying all these to.
        self.master = master
        # Give the window a name
        master.title("Export Layers - with checkboxes and radiobuttons")

        # Size
        master.geometry(geometry)
        self.width  = int(geometry.split("x", 1)[0])
        self.height = int(geometry.split("x", 1)[1].split("+")[0])

        # These are to pass stuff around the gui and the external functions
        self.kwargs  = dict()
        self.lastdir = '/'

        # Input Validation for fields that take only numbers
        vcmd = (master.register(self.validate_numbers))
        vcmd2 = (master.register(self.validate_layerfilter))

        # These are all the GUI Items--------------------------

        # Frames & Status Bar
        self.right_frame  = tk.LabelFrame(self.master, text="PSD layers", padx=5, height=self.height-40, width=int(self.width/2)-10 )
        self.left_frame   = tk.Frame(self.master, padx=5, height=self.height-40, width=int(self.width/2)-10,)  
        self.status_bar   = tk.Label(self.master, text="", bd=1, relief=tk.SUNKEN, width=60)
        
        self.left_frame.grid(row = 0, column = 0,  sticky = tk.W, pady = 5, padx = 5)
        self.right_frame.grid(row = 0, column = 1, pady = 5, padx = 5, sticky=tk.E)
        self.status_bar.grid(row = 1, column = 0, columnspan=2,sticky = tk.S)

        # This is the PSD info text (currently number of layers and number of folders). It's initilized with ""
        self.psdinfo      = scrolledtext.ScrolledText(self.right_frame, width=45, wrap=tk.WORD, state="disabled", spacing1=1)   
        self.psdinfo.grid(row=0, column=0)

        # open file button, calls select_file
        self.open_button  = ttk.Button(self.left_frame, text='Open PSD', command=self.select_file)
        self.open_button.grid(row = 0, column = 0, columnspan = 2, pady = 2)
        
        # thumbnails (gets grid-ed when opening a file.)
        self.thumbnail    = tk.Label(self.left_frame)
        
        # Export
        self.export_button = ttk.Button(self.left_frame, text='Export Layers',command=self.export_psd)

        # ignore invisible checkbox
        self.ignore_invisible = tk.BooleanVar(value=True)
        self.ignore_invisible_check = ttk.Checkbutton(self.left_frame, text = "Ignore invisible Layers/Groups", variable=self.ignore_invisible, onvalue=True, offvalue=False, command=lambda:self.toggle_kwargs("ignore_invisible"))

        # crop to mask checkbox
        self.trim_to_mask = tk.BooleanVar(value=False)
        self.trim_to_mask_check = ttk.Checkbutton(self.left_frame, text = "Crop to mask size if present (overrides trim)", variable=self.trim_to_mask, onvalue=True, offvalue=False, command=lambda:self.toggle_kwargs("trim_to_mask"))
        
        # Trim & Crop behavior
        self.trim_frame = tk.LabelFrame(self.left_frame, text="Trim...", padx=5)

        # trim 
        self.trim = tk.StringVar(value="all")
        # trim transparent for each layer.
        self.trim_layers_radio = ttk.Radiobutton(self.trim_frame, text = "Trim transparent parts (each layer)", variable=self.trim, value="all", command=self.toggle_trim)
        # trim visible full psd
        self.trim_to_visible_radio = ttk.Radiobutton(self.trim_frame, text = "Trim transparent parts (full image)", variable=self.trim, value="visible",  command=self.toggle_trim)
        # do not trim
        self.dont_trim_radio = ttk.Radiobutton(self.trim_frame, text = "Don't trim (export at canvas size)", variable=self.trim, value="canvas",  command=self.toggle_trim)
        
        # Resize
        self.resize_frame = tk.LabelFrame(self.left_frame, text="Size", padx=5)
        # Width input
        self.width_input = tk.IntVar(value=100, name="width_input")
        self.width_input_entry = tk.Entry(self.resize_frame, name="w_entry", textvariable = str(self.width_input), width=5, validate="all", validatecommand=(vcmd, '%P')) # type: ignore

        # height input
        self.height_input = tk.IntVar(value=100, name="height_input")
        self.height_input_entry = tk.Entry(self.resize_frame, name="h_entry", textvariable = str(self.height_input), width=5,validate="all", validatecommand=(vcmd, '%P')) # type: ignore
       
        # binding the entry fields
        self.resize_focus = tk.StringVar(value="", name="resize_focus")
        self.width_input_entry.bind("<FocusIn>",self.resize_set_focus) 
        self.height_input_entry.bind("<FocusIn>",self.resize_set_focus)

        # registering the variable observers
        self.width_input.trace_add('write', self.resize_callback)
        self.height_input.trace_add('write', self.resize_callback)

        # Ratio checkbox
        self.aspect_ratio = tk.BooleanVar(value=True)
        self.aspect_ratio_check = ttk.Checkbutton(self.resize_frame, text = "maintain aspect ratio", variable=self.aspect_ratio, onvalue=True, offvalue=False, command=self.toggle_aspect_ratio)
        
        # Dropdown pix vs percent
        self.resize_type_choices = ["%","px"]
        self.resize_type = tk.StringVar(value="%")
        self.resize_type_menu = ttk.OptionMenu(self.resize_frame, self.resize_type, "%", *self.resize_type_choices, command=self.percent_pixel_switch)

        # Filter
        self.filter_frame = tk.LabelFrame(self.left_frame, text="Filter", padx=5)

        #Filter variables
        self.selected = tk.StringVar(value="",name="selected")
        self.flatten = tk.StringVar(value="",name="flatten")
        self.selected_action = tk.StringVar(value="export", name="selected_action")
        self.flatten_action = tk.StringVar(value="flatten", name="flatten_action")

        #Input
        self.selected_entry = tk.Entry(self.filter_frame, name="selected_entry", textvariable = self.selected, validate="all", validatecommand=(vcmd2, '%P'))
        self.flatten_entry = tk.Entry(self.filter_frame, name="flatten_entry", textvariable = self.flatten, validate="all", validatecommand=(vcmd2, '%P'))
        #Radio
        self.ignore_selected_radio = ttk.Radiobutton(self.filter_frame, text = "Ignore selected", variable=self.selected_action, value="ignore", command=lambda:self.toggle_kwargs("selected_action"))
        self.export_selected_radio = ttk.Radiobutton(self.filter_frame, text = "Export only selected", variable=self.selected_action, value="export", command=lambda:self.toggle_kwargs("selected_action"))
        self.ignore_flatselected_radio = ttk.Radiobutton(self.filter_frame, text = "Flatten selected", variable=self.flatten_action, value="flatten", command=lambda:self.toggle_kwargs("flatten_action"))
        self.export_flatselected_radio = ttk.Radiobutton(self.filter_frame, text = "Flaten all BUT selected", variable=self.flatten_action, value="ignore", command=lambda:self.toggle_kwargs("flatten_action"))

    #----------------------------------------- 
    # Packing Export GUI

    def show_export_gui(self):
        """Shows exporting gui"""
        # row 2: EXPORT BUTTON
        self.export_button.grid(row = 2, column = 0, pady = 2)
        
        # row 3-5
        tk.Label(self.left_frame, text="").grid(row = 3, column = 0, pady=1, sticky=tk.W) # <- temp space
        self.ignore_invisible_check.grid(row = 4, column = 0, pady=2, sticky=tk.W)
        self.trim_to_mask_check.grid(row = 5, column = 0, pady=1, sticky=tk.W)
        
        # row 6: TRIM
        self.trim_frame.grid(row = 6, column = 0, pady=2, sticky=tk.W)
        # trim to layer
        self.trim_layers_radio.grid(row = 1, column = 0, pady=1, sticky=tk.W)
        # trim to visible
        self.trim_to_visible_radio.grid(row = 2, column = 0, pady=1, sticky=tk.W)
        # export everything at full canvas size
        self.dont_trim_radio.grid(row = 3, column = 0, pady=1, sticky=tk.W)
        
        # row 7: Resize
        self.resize_frame.grid(row=7,column = 0, pady=2, sticky=tk.W)

        tk.Label(self.resize_frame, text="W:").grid(row = 1, column = 0, pady=1, sticky=tk.W)
        self.width_input_entry.grid(row = 1, column = 1, pady=1, sticky=tk.W)
        tk.Label(self.resize_frame, text="x H:").grid(row = 1, column = 2, pady=1, sticky=tk.W)
        self.height_input_entry.grid(row = 1, column = 3, pady=1, sticky=tk.W)
        self.resize_type_menu.grid(row = 1, column = 4, pady=1, sticky=tk.W)
        self.aspect_ratio_check.grid(row = 2, column = 0, pady=1,columnspan=4)

        #row 8: Filter
        self.filter_frame.grid(row=8,column = 0, pady=2, sticky=tk.W)
        
        tk.Label(self.filter_frame, text="Separate names with commas. Can use *.").grid(row = 0, column = 0, pady=1, sticky=tk.W,columnspan=4)
        tk.Label(self.filter_frame, text="Select").grid(row = 1, column = 0, pady=1, sticky=tk.W)
        self.selected_entry.grid(row = 1, column = 1, pady=1, sticky=tk.W)
        self.ignore_selected_radio.grid(row = 2, column = 0, pady=1, sticky=tk.W,columnspan=4)
        self.export_selected_radio.grid(row = 3, column = 0, pady=1, sticky=tk.W,columnspan=4)
        tk.Label(self.filter_frame, text="Flatten").grid(row = 4, column = 0, pady=1, sticky=tk.W)
        self.flatten_entry.grid(row = 4, column = 1, pady=1, sticky=tk.W)
        self.ignore_flatselected_radio.grid(row = 5, column = 0, pady=1, sticky=tk.W,columnspan=4)
        self.export_flatselected_radio.grid(row = 6, column = 0, pady=1, sticky=tk.W,columnspan=4)


    def show_thumb(self, thumb):
        """Shows the thumbnail"""
        if thumb:
            thumb = ImageTk.PhotoImage(thumb)
            self.thumbnail.config(image = thumb)
            self.thumbnail.image = thumb #type: ignore 
            self.thumbnail.grid(row = 1, column = 0, columnspan = 2, pady = 2)

    def show_tree(self):
        """Function to show psd layers and folders"""

        #use self.kwargs to access the psd file
        psd, psd_name, *_ = self.kwargs["file"].values()

        #update status bar
        self.status_bar.config(text="Opening Layer structure...")
        self.master.update_idletasks()

        #Update status bar
        self.status_bar.config(text="Done!")
        self.master.update_idletasks()

        #Update psd info to show the tree using get_repr
        self.psdinfo.config(state=tk.NORMAL)
        self.psdinfo.insert(tk.END,get_repr(psd))
        self.psdinfo.config(state=tk.DISABLED)

        self.right_frame.config(text=str(psd_name))

    def reset_tree(self):
        """Clears the testfield that shows the tree"""
        self.psdinfo.config(state=tk.NORMAL)
        self.psdinfo.delete("1.0", tk.END) #???
        self.psdinfo.config(state=tk.DISABLED)
    
    #--------------------------------
    # METHODS used inside the app 

    def retrieve_filter_kwargs(self):
        # get the vars
        selected = separate_filters(self.selected.get())#["*layer*"]
        flatten = separate_filters(self.flatten.get())
        selected_action = self.selected_action.get()
        flatten_action = self.flatten_action.get()
        selected_action = selected_action if selected_action in ["ignore","export"] else None
        flatten_action = flatten_action if flatten_action in ["ignore","flatten"] else None

        self.kwargs["selected"]=selected
        self.kwargs["flatten"]=flatten
        self.kwargs["selected_action"] = selected_action
        self.kwargs["flatten_action"] = flatten_action


    def resize_set_focus(self,event):
        """Callback for when a widget is focused, sets resize_focus to the name of the widget."""
        name = str(event.widget).split(".")[-1]
        self.resize_focus.set(name)

    def validate_numbers(self,P):
        """
        Validation function to allow only digits and deletion.
        %P represents the value the text will have if the change is allowed.
        """
        if P.isdigit():
            return True
        else:
            return False
        
    def validate_layerfilter(self,text):
        """Validation function to allow only digits, letters, underscores and commas"""
        if text == "":
            return True
        match = re.fullmatch(r"[a-zA-Z0-9 _,*-><]+",text)
        return match is not None


    def reset_variables(self):
        """Resets all 'screen' variables to their default values."""
        self.ignore_invisible.set(True)
        self.trim_to_mask.set(False)
        self.trim.set("all")
        self.resize_type.set("%")
        self.width_input.set(100)
        self.height_input.set(100)
        self.aspect_ratio.set(True)
    
    def resize_callback(self, var, *args):
        """Observer for size input that modifies the value not being edited in real time"""

        width   = self.width_input.get()
        height  = self.height_input.get()
        keep    = self.aspect_ratio.get()
        kind    = self.resize_type.get()
        focus   = self.resize_focus.get()
        og_size = self.kwargs["file"]["psd_size"]

        # defining callables
        set_height = self.height_input.set
        set_width  = self.width_input.set
        px_resize  = partial(get_resize,size=og_size,kind="px")

        #check if aspect ratio is selected, otherwise do nothing.
        if not keep:
            return
        
        # if we're in %, make sure height and width are the same
        if kind == "%":
            if var == "width_input" and focus == "w_entry":
                set_height(width)
            elif var == "height_input" and focus == "h_entry":
                set_width(height)
            
        # if we're in pixels
        else:

            if var == "width_input" and focus == "w_entry":
                set_height(px_resize(width=width))

            elif var == "height_input" and focus == "h_entry":
                set_width(px_resize(height=height))
                
    def percent_pixel_switch(self,choice):
        """switches between percent and pixel entries."""
        
        kind = self.resize_type.get()

        # if we're not changing anything, don't do anything.
        if kind == self.kwargs["kind"]:
            return
        
        # save kind
        self.kwargs["kind"] = kind

        # og size & size from input
        og_size    = self.kwargs["file"]["psd_size"]
        input_size = (int(self.width_input.get()), int(self.height_input.get() ))

        #convert the input
        nw, nh = size_convert(og_size,input_size,kind=kind)

        # set vars to new values
        self.width_input.set(int(nw))
        self.height_input.set(int(nh)) 
      
    def toggle_aspect_ratio(self):
        """Activates 'keep aspect ratio', 
        which makes sure that when one value is altered, 
        the other is altered in proportion."""

        keep   = self.aspect_ratio.get() # keep aspect ratio toggle
        kind   = self.resize_type.get()  # px / % toggle
        focus  = self.resize_focus.get() # last field focused
        width  = self.width_input.get()
        height = self.height_input.get()
        
        # if we're not changing it, don't do anything
        if keep == self.kwargs["keep_aspect_ratio"]:
            return
        
        # defining simpliified callables 
        set_height = self.height_input.set
        set_width  = self.width_input.set
        
        # if activating aspect ratio
        if keep:
            # if we're using %, copy the number from whatever was focused last
            if kind == "%": 
                if focus == "w_entry":
                    set_height(width)
                else:
                    set_width(height)
                
            # if we're doing pixels, also use the last focus as source, and make sure height entry is tracking height and not width.
            else:
                
                # simplified callable
                px_resize = partial(get_resize,size=self.kwargs["file"]["psd_size"],kind="px")

                if focus == "w_entry":        
                    set_height(px_resize(width=width))
                else:
                    set_width(px_resize(height=height))

        
        # if we're disabling ratio, make sure to copy % still before doing anything.
        elif kind == "%": 
            set_height(width)
                        
        # save it.
        self.kwargs["keep_aspect_ratio"] = keep
    
    def toggle_trim(self):
        """Toggles several kwargs related to trimming/cropping"""

        trim = self.trim.get()

        if trim == "all":
            # trims each layer's transparency
            self.kwargs["trim_layers"]     = True
            self.kwargs["trim_to_visible"] = False

        elif trim == "visible":
            # saves visible bbox of WHOLE PSD and saves each layer to that size
            self.kwargs["trim_layers"]     = False
            self.kwargs["trim_to_visible"] = True

        else:
            # Do not trim transparency
            self.kwargs["trim_layers"]     = False
            self.kwargs["trim_to_visible"] = False

    def toggle_kwargs(self,toggle):
        """Toggles a kwarg"""
        var = getattr(self,toggle).get()
        self.kwargs[toggle] = var

    def select_file(self):
        """Function to pick a file in the OS file picker"""

        # filetypes for the tkinter dialogue
        filetypes = (('PSD files', '*.psd'), ('All files', '*.*'))

        # this opens an open file window.
        filename  = fd.askopenfilename(title='Open a psd file', filetypes=filetypes, initialdir=self.lastdir)

        # this is to set the open file starting dir to the path of the last opened file next time it's used.
        self.lastdir = get_psd_dir(filename)

        # if we opened a file, read it
        if filename:
            result = self.open_psd(filename)
        
    def kwargs_init(self,result):
        self.kwargs = dict()
        self.kwargs["file"] = result
        self.kwargs["width"], self.kwargs["height"] = result["psd_size"]
        self.kwargs["kind"] = "%"
        self.kwargs["keep_aspect_ratio"] = True
        
    def open_psd(self, filename):
        """Function to open a PSD file and read it"""

        # call the external open_psd func (in psd_funcs.py)
        result = open_psd(filename)
        
        # if it didn't work, return
        if not result:
            self.status_bar.config(text = "Couldn't read the file")
            return result

        # update text of status bar
        self.status_bar.config(text = "Opened "+ result["psd_name"]) # type: ignore
        
        # init kwargs & variables and reset tree
        self.kwargs_init(result)
        self.reset_variables()
        self.reset_tree()

        # show thumbnail, export forms and the tree
        self.show_thumb(get_psd_thumbnail(result["psd"]))
        self.show_export_gui()
        self.show_tree()
    
    def retrieve_input_kwargs(self):
        """retrieves ALL the relevant values from input fields, radiobuttons and checkboxes and stores them in kwargs for exporting"""
        
        # retrieve filters
        self.retrieve_filter_kwargs()

        # get og size
        og_size = self.kwargs["file"]["psd_size"]

        # retrieve input_w, input_h, kind and aspect ratio
        iw, ih                           = self.width_input.get(), self.height_input.get() 
        self.kwargs["kind"]              = self.resize_type.get()
        self.kwargs["keep_aspect_ratio"] = self.aspect_ratio.get()

        # if w and/or h are 0, set them to 1
        iw = 1.0 if iw in [0,"0",""] else float(iw)
        ih = 1.0 if ih in [0,"0",""] else float(ih) 

        # If we keep aspect ratio
        if self.kwargs["keep_aspect_ratio"]:
            
            # if we were retrieving %, save that as scale
            if self.kwargs["kind"] == "%":
                self.kwargs["scale"] = iw/100
                
            # if we were retrieving px, get the % by dividing new size and og size
            else:
                self.kwargs["scale"] = iw/og_size[0]

            # save new height and width. This will be the new max canvas size.
            self.kwargs["width"], self.kwargs["height"] = [i * self.kwargs["scale"] for i in og_size]

        
        # if we're NOT keeping the aspect ratio
        else:
            #set scale to something else so the function knows it has to resize
            self.kwargs["scale"] = 1.1

            # if we were retrieving %, multiply that to the og sizes and store them.
            if self.kwargs["kind"] == "%":
                self.kwargs["width"]  = get_resize(og_size, width  = iw, convert = True)
                self.kwargs["height"] = get_resize(og_size, height = ih, convert = True)

            # if we were retrieving px, just save those.
            else:
                self.kwargs["width"], self.kwargs["height"] = int(iw), int(ih)
    
    def export_psd(self, flat=False):
        """Function that calls other exporter functions, for the PSDImage file"""

        # use self.kwargs to access the psd file and get its name without .psd
        psd, psd_name, *_ = self.kwargs["file"].values()
        name = psd_name.removesuffix(".psd")

        # Open a save_as window.
        path  = fd.askdirectory(title = 'Choose where to save', initialdir = self.lastdir)

        # if user cancels
        if not path:
            return
        
        # Make a path for the new folder where we'll be saving things - default behavior
        path = path+"/"+name

        # Create the main folder
        Path(path).mkdir(parents=True, exist_ok=True)

        # Get the args we'll pass to the function
        self.retrieve_input_kwargs()
        export_args = get_export_args(**self.kwargs)
        export_args["flat"] = flat
        if flat:
            export_args["flatten"].append("*")

        # Call external save function
        result = process_psd(psd, name, path, **export_args)
        
        # Update status bar
        if result == True:
            self.status_bar.config(text="Exported "+psd_name+" at "+path+"/" )
            
        else:
            self.status_bar.config(text=result)
        
        self.master.update_idletasks()

               
def main():
    # create the root window
    root = tk.Tk()
    w=700
    h=700
    app = App(root,f"{w}x{h}+400+300")

    # run the application
    root.mainloop()

if __name__ == "__main__":
    main()

