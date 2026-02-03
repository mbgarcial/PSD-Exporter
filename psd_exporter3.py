

from psd_funcs2 import *
import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog as fd #This is for opening files
import tkinter.scrolledtext as scrolledtext
from PIL import ImageTk


#TODO NEXT:

# - Resize!!

# - Make widget size bigger to fit the window

#-------------------------------------------------------------------------------------------
# This version shows non-expandable tree on opening, and has buttons to export layers.
# Default behavior is:
#       - export layers trimmed of blank pixels OR document size OR visible PSD size
#       - ignore invisible layers
#       - ignore clipping layers when exporting, and apply them to layers that have them
#       - apply masks to layers (NOT GROUPS) that have them
#       - create new folders for groups and export their contents
#       - if a group has a mask, apply it to all its children.
#       - crop layer/group's children to mask size
#-------------------------------------------------------------------------------------------
# CREDITS:
# How to add an image in tkinter: https://www.geeksforgeeks.org/python/how-to-add-an-image-in-tkinter/
# Save pil image with saveasfile tkinter: https://www.daniweb.com/programming/software-development/threads/520677/how-to-save-the-edited-photo-tkinter-as-jpg-with-asksaveasfilename#:~:text=Dani%20AI,image%20as...'%2C

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
        self.args    = list()
        self.kwargs  = dict()
        self.lastdir = '/'

        # Input Validation for fields that take only numbers
        vcmd = (master.register(self.validate_numbers))

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

        # trim transparent checkbox
        self.trim = tk.StringVar(value="all")
        self.trim_layers_radio = ttk.Radiobutton(self.trim_frame, text = "Trim transparent parts (each layer)", variable=self.trim, value="all", command=self.toggle_trim)
        # trim full psd
        self.trim_to_visible_radio = ttk.Radiobutton(self.trim_frame, text = "Trim transparent parts (full image)", variable=self.trim, value="visible",  command=self.toggle_trim)
        # do not trim
        self.dont_trim_radio = ttk.Radiobutton(self.trim_frame, text = "Don't trim (export at canvas size)", variable=self.trim, value="canvas",  command=self.toggle_trim)
        
        # Resize
        self.resize_frame = tk.LabelFrame(self.left_frame, text="Size", padx=5)
        # Width input
        self.width_input = tk.StringVar(value="100")
        self.width_input_entry = tk.Entry(self.resize_frame, textvariable = self.width_input, width=5, validate="all", validatecommand=(vcmd, '%P'))
        
        # height input
        self.height_input = tk.StringVar(value="100")
        self.height_input_entry = tk.Entry(self.resize_frame, textvariable = self.width_input, width=5,validate="all", validatecommand=(vcmd, '%P'))
        
        # Ratio checkbox
        self.aspect_ratio = tk.BooleanVar(value=True)
        self.aspect_ratio_check = ttk.Checkbutton(self.resize_frame, text = "maintain aspect ratio", variable=self.aspect_ratio, onvalue=True, offvalue=False, command=self.toggle_aspect_ratio)
        
        # Dropdown pix vs percent
        self.resize_type_choices = ["%","px"]
        self.resize_type = tk.StringVar(value="%")
        self.resize_type_menu = ttk.OptionMenu(self.resize_frame, self.resize_type, "%", *self.resize_type_choices, command=self.percent_pixel_switch)

        #⚠️ TEMP
        #self.scale_50 = tk.BooleanVar(value=False)
        #⚠️ Export Resized!
        #self.scale_50_check = ttk.Checkbutton(self.left_frame, text = "Scale to 50% when exporting", variable=self.scale_50, onvalue=True, offvalue=False, command=self.toggle_scale_50)
        #⚠️ Export at 300 px wide
        #self.scale_50_check = ttk.Checkbutton(self.left_frame, text = "Export at 300px wide (maintain ratio)", variable=self.scale_50, onvalue=True, offvalue=False, command=self.toggle_scale_50)
        #⚠️ Export at 500 px height
        #self.scale_50_check = ttk.Checkbutton(self.left_frame, text = "Export at 500px height (maintain ratio)", variable=self.scale_50, onvalue=True, offvalue=False, command=self.toggle_scale_50)

    def show_export_gui(self):
        """Shows exporting gui"""
        # row 2
        self.export_button.grid(row = 2, column = 0, pady = 2)
        # row 3-5
        tk.Label(self.left_frame, text="").grid(row = 3, column = 0, pady=1, sticky=tk.W) # <- temp
        self.ignore_invisible_check.grid(row = 4, column = 0, pady=2, sticky=tk.W)
        self.trim_to_mask_check.grid(row = 5, column = 0, pady=1, sticky=tk.W)
        # row 6
        self.trim_frame.grid(row = 6, column = 0, pady=2, sticky=tk.W)
        self.trim_layers_radio.grid(row = 1, column = 0, pady=1, sticky=tk.W)
        self.trim_to_visible_radio.grid(row = 2, column = 0, pady=1, sticky=tk.W)
        self.dont_trim_radio.grid(row = 3, column = 0, pady=1, sticky=tk.W)
        
        # row 7
        self.resize_frame.grid(row=7,column = 0, pady=2, sticky=tk.W)

        tk.Label(self.resize_frame, text="W:").grid(row = 1, column = 0, pady=1, sticky=tk.W)
        self.width_input_entry.grid(row = 1, column = 1, pady=1, sticky=tk.W)
        tk.Label(self.resize_frame, text="x H:").grid(row = 1, column = 2, pady=1, sticky=tk.W)
        self.height_input_entry.grid(row = 1, column = 3, pady=1, sticky=tk.W)
        self.height_input_entry.config(state="disabled")
        self.resize_type_menu.grid(row = 1, column = 4, pady=1, sticky=tk.W)
        self.aspect_ratio_check.grid(row = 2, column = 0, pady=1,columnspan=4)

    def percent_pixel_switch(self,choice):
        """switches between percent and pixel entries."""
        kind = self.resize_type.get()
        #print("Pixel to percent switch!!", choice)

        # if we're not changing anything, don't do anything.
        if kind == self.kwargs["kind"]:
            return
        
        nw, nh = str(100),str(100)
        
        # og size
        ow, oh = self.kwargs["file"]["psd_size"]
        # get w & h values from input
        iw,ih = self.width_input.get(), self.height_input.get() 
        
        # if we're changing from px to %:
        if kind == "%":
            # get the % from og
            nw = round((100/ow)*float(iw))
            nh = round((100/ow)*float(ih))
            
        # if we're changing from % input to pixels
        elif kind == "px":
            # multiply og size with input %
            nw, nh = int(ow*float(iw)/100), int(oh*float(ih)/100)     

        # save kind
        self.kwargs["kind"] = kind
        # set vars to new values
        self.width_input.set(str(nw))
        self.height_input.set(str(nh)) 
        
    def get_psd_ratio(self) -> float:
        """get the aspect ratio"""
        psd = self.kwargs.get("file",None)

        if not psd:
            return 1.0

        return psd.size[0]/psd.size[1]
    
    def validate_numbers(self,P):
        """
        Validation function to allow only digits and deletion.
        %P represents the value the text will have if the change is allowed.
        """
        if P.isdigit() or P == "":
            return True
        else:
            return False

    def retrieve_input_kwargs(self):
        """retrieves the values from input fields and stores them in kwargs when exporting"""
        # get og size
        og_size = self.kwargs["file"]["psd_size"]

        # retrieve input_w, input_h, kind and aspect ratio
        self.kwargs["kind"] = self.resize_type.get()
        iw,ih = self.width_input.get(), self.height_input.get() 
        self.kwargs["keep_aspect_ratio"] = self.aspect_ratio.get()

        # If we keep aspect ratio
        if self.kwargs["keep_aspect_ratio"]:
            
            # if we were retrieving %, save that as scale
            if self.kwargs["kind"] == "%":
                self.kwargs["scale"] = float(iw)/100
                #print("retrieving scale when kind is %:",self.kwargs["scale"])

            # if we were retrieving px, get the % by multiplying the og size and the new size (?)
            else:
                self.kwargs["scale"] = ((float(iw)/og_size[0]))

                #print("retrieving scale when kind is px:",self.kwargs["scale"])

            self.kwargs["width"], self.kwargs["height"] = [i*self.kwargs["scale"] for i in og_size]

        # if we're not keeping the aspect ratio...
        else:
            #set scale to something else so it knows it has to resize
            self.kwargs["scale"] = 1.1

            # if we were retrieving %, multiply that to the og sizes and store them.
            if self.kwargs["kind"] == "%":
                self.kwargs["width"]  = int(float(iw)/100*og_size[0])
                self.kwargs["height"] = int(float(ih)/100*og_size[1])

            # if we were retrieving px, just save those.
            else:
                self.kwargs["width"], self.kwargs["height"] = int(iw), int(ih)
        

    def toggle_aspect_ratio(self):
        val = self.aspect_ratio.get()
        self.kwargs["keep_aspect_ratio"] = val
        if val:
            # if keeping aspect ratio, disable height.
            self.height_input_entry.config(state="disabled",disabledbackground="light gray", textvariable=self.width_input)
            self.height_input.set(self.width_input.get())
        else:
            self.height_input.set(self.width_input.get())
            self.height_input_entry.config(state="normal",textvariable=self.height_input)


    def toggle_trim(self):
        """Toggles several kwargs related to trimming/cropping"""
        val = self.trim.get()
        if val == "all":
            self.kwargs["trim_layers"]     = True
            self.kwargs["trim_to_visible"] = False
        elif val == "visible":
            self.kwargs["trim_layers"]     = False
            self.kwargs["trim_to_visible"] = True
        else:
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

        # this is to set the open file starding dir to the path of the last opened file next time it's used.
        match = re.match(r"(.*/).*\.psd",filename)
        if match:
            self.lastdir = match.group(1)

        # if we opened a file, read it
        if filename:
            result = self.open_psd(filename)
            #if reading the file was successful, assign its result to the app to pass it to other funcs.
            if result:
                self.kwargs["file"] = result
                self.kwargs["kind"] = "%"
                self.kwargs["width"], self.kwargs["height"] = result["psd_size"]
                self.show_tree()
        
    def open_psd(self, filename):
        """Function to open a PSD file and read it"""

        # call the external open_psd func (in psd_funcs.py)
        result = open_psd(filename)
        thumb = result["psd"].thumbnail()
        if not thumb:
            image = result["psd"].composite(apply_icc=False)
            w, h = image.size
            new_h = 120
            new_w = int(1/(h/w) * new_h)
            thumb = image.resize((new_w, new_h))

            #thumb.save("thumb.png")
        if thumb:
            thumb = ImageTk.PhotoImage(thumb)

        # update text of status bar
        if not result:
            self.status_bar.config(text = "Couldn't read the file")
        else:
            self.status_bar.config(text = "Opened "+ result["psd_name"]) #type:ignore
            # show the thumbnail
            if thumb:
                self.thumbnail.config(image = thumb)
                self.thumbnail.image = thumb #type: ignore 
                self.thumbnail.grid(row = 1, column = 0, columnspan = 2, pady = 2)
            #else:
            #    self.thumbnail.pack_forget()
            # reset tree
            self.psdinfo.config(state=tk.NORMAL)
            self.psdinfo.delete("1.0", tk.END) #???
            self.psdinfo.config(state=tk.DISABLED)

            # show the export stuff
            self.show_export_gui()

        # return the result of the read psd func (a dict that's empty if it fails)
        return result
    
    def export_psd(self, flat=False):
        """Function that calls other exporter functions, for the PSDImage file"""

        # use self.kwargs to access the psd file
        psd, psd_name, *_ = self.kwargs["file"].values()

        # get the name of the psd.
        name = psd_name.removesuffix(".psd")

        # this opens a save_as window.
        path  = fd.askdirectory(title = 'Choose where to save', initialdir = self.lastdir)

        # if user cancels
        if not path:
            return
        
        # Make a path for the new folder where we'll be saving things - default behavior
        path = path+"/"+name
        Path(path).mkdir(parents=True, exist_ok=True)

        #get the args we'll pass to the function
        self.retrieve_input_kwargs()
        export_args = get_export_args(**self.kwargs)
        export_args["flat"] = flat

        # Call external save function
        result = process_psd(psd, name, path, **export_args)
        
        # update status bar
        if result == True:
            self.status_bar.config(text="Exported "+psd_name+" at "+path+"/" )
            
        else:
            self.status_bar.config(text=result)
        
        self.master.update_idletasks()

    def show_tree(self):
        """Function to count psd layers and folders"""

        #use self.kwargs to access the psd file
        psd, psd_name, *_ = self.kwargs["file"].values()

        #update status bar
        self.status_bar.config(text="Opening Layer structure...")
        self.master.update_idletasks()


        #Update status bar
        self.status_bar.config(text="Done!")
        self.master.update_idletasks()

        #Update PSD info
        self.psdinfo.config(state=tk.NORMAL)
        self.psdinfo.insert(tk.END,get_repr(psd))
        self.psdinfo.config(state=tk.DISABLED)

        self.right_frame.config(text=str(psd_name))

               
def main():
    # create the root window
    root = tk.Tk()
    w=700
    h=500
    app = App(root,f"{w}x{h}+400+300")


    # run the application
    root.mainloop()

if __name__ == "__main__":
    main()

