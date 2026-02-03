

from psd_funcs import *
import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog as fd #This is for opening files
import tkinter.scrolledtext as scrolledtext
from PIL import ImageTk
#from pathlib import Path



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
        master.title("Export Layers and Trim")

        # Size
        master.geometry(geometry)
        self.width  = int(geometry.split("x", 1)[0])
        self.height = int(geometry.split("x", 1)[1].split("+")[0])

        # These are to pass stuff around the gui and the external functions
        self.args    = list()
        self.kwargs  = dict()
        self.lastdir = '/'

        # These are frames to put widgets into. two frames side by side, then another one at the bottom.
        self.frame = tk.Frame(master, padx=5, width=self.width, height=self.height-100)
        
        self.left_frame   = tk.Frame(self.frame, padx=5, width=self.width/2, height=self.height-20)  
        self.right_frame  = tk.LabelFrame(self.frame, text="PSD layers", padx=5, width=self.width/2, height=self.height-20)
        self.bottom_frame = tk.Frame(master, width=self.width)
        
        self.frame.pack()
        self.frame.pack_propagate(False)

        self.left_frame.pack(fill = "both", expand = 1, side = "left")
        self.left_frame.pack_propagate(False)

        self.right_frame.pack(fill = "both", expand = 1, side = "right")
        self.right_frame.pack_propagate(False)

        self.bottom_frame.pack(side=tk.BOTTOM)

        # open file button, calls select_file
        self.open_button  = ttk.Button(self.left_frame, text='Open PSD', command=self.select_file)

        # ignore invisible checkbox
        self.ignore_invisible = tk.BooleanVar()
        self.ignore_invisible_check = ttk.Checkbutton(self.left_frame, text = "Ignore invisible Layers/Groups", variable=self.ignore_invisible, onvalue=True, offvalue=False, command=lambda:self.toggle_kwargs("ignore_invisible"))
        


        # Cropping and Trimming
        # trim all layers checkbox
        # trim to mask size checkbox (overrides trim layers)
        # crop to visible layers

        # TEMP EXPORT PSD LAYERS BUTTONS ==================

        # ignore invisible, trim layers, don't trim to mask
        self.export_folders_button = ttk.Button(self.left_frame, text='Export at layer size (ignore invisible)',command=self.export_psd_folders)

        # don't ignore invisible, trim layers, don't trim to mask
        self.export_invisibles_button = ttk.Button(self.left_frame, text='Export at layer size (not ignore invisible)',command=self.export_psd_folders_invisible)

        # ignore invisible, don't trim layers, don't trim to mask
        self.export_canvas_size_button = ttk.Button(self.left_frame, text='Export at canvas size (ignore invisible)',command=self.export_psd_canvas_size)

        # ignore invisible, don't trim layers, trim to mask
        self.export_mask_trim_button = ttk.Button(self.left_frame, text='Export at canvas size + mask trim',command=self.export_psd_trim_to_mask)

        # ignore invisible, trim layers, trim to mask
        self.export_trim_both_button = ttk.Button(self.left_frame, text='Export at layer size + mask trim',command=self.export_psd_trim_both)

        # ignore invisible, don't trim layers, don't trim to mask, trim to full visible psd
        self.export_trim_visible_button = ttk.Button(self.left_frame, text='Export at visible psd size',command=self.export_psd_trim_visible)

        #==================================================

        # This is the PSD info text (currently number of layers and number of folders). It's initilized with ""
        self.psdinfo      = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD,width=int(self.width/2-10), state="disabled", spacing1=1)
        
        # Statusbar at the bottom
        self.status_bar   = tk.Label(self.bottom_frame, text="", bd=1, relief=tk.SUNKEN, anchor=tk.CENTER, width=40)
        
        self.thumbnail    = tk.Label(self.left_frame)
        # Pack the widgets.
        # The tree_button & thumbnail only get packed after opening a file.
        self.open_button.pack(expand=True)
        self.psdinfo.pack(expand=True, fill="both")
        self.status_bar.pack()

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
            result = self.read_psd(filename)
            #if reading the file was successful, assign its result to the app to pass it to other funcs.
            if result:
                self.kwargs["file"] = result
                self.show_tree()
        
    def read_psd(self, filename):
        """Function to open a PSD file and read it"""

        # call the external read_psd func (in psd_funcs.py)
        result = read_psd(filename)
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
                self.thumbnail.pack(expand = True)
            else:
                self.thumbnail.pack_forget()
            # reset tree
            self.psdinfo.config(state=tk.NORMAL)
            self.psdinfo.delete("1.0", tk.END) #???
            self.psdinfo.config(state=tk.DISABLED)

            # pack the export button(s)
            self.ignore_invisible_check.pack(pady=10)
            self.export_trim_visible_button.pack(expand=True)
            self.export_trim_both_button.pack(expand=True)
            self.export_mask_trim_button.pack(expand=True)
            self.export_canvas_size_button.pack(expand=True)
            self.export_folders_button.pack(expand=True)
            self.export_invisibles_button.pack(expand=True)



        # return the result of the read psd func (a dict that's empty if it fails)
        return result
    
    def export_psd(self, flat=False):
        """Function that calls other exporter functions, for the PSDImage file"""

        # use self.kwargs to access the psd file
        psd, psd_name = self.kwargs["file"].values()

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


    def export_psd_folders(self):
        #self.kwargs["ignore_invisible"] = True
        self.kwargs["trim_layers"] = True
        self.kwargs["trim_to_mask"] = False
        self.kwargs["trim_to_visible"] = False
        self.export_psd()

    def export_psd_folders_invisible(self):
       
        #self.kwargs["ignore_invisible"] = False
        self.kwargs["trim_layers"] = True
        self.kwargs["trim_to_mask"] = False
        self.kwargs["trim_to_visible"] = False
        self.export_psd()

    def export_psd_canvas_size(self):
      
        #self.kwargs["ignore_invisible"] = True
        self.kwargs["trim_layers"] = False
        self.kwargs["trim_to_mask"] = False
        self.kwargs["trim_to_visible"] = False
        self.export_psd()
    
    def export_psd_trim_to_mask(self):
        
        #self.kwargs["ignore_invisible"] = True
        self.kwargs["trim_layers"] = False
        self.kwargs["trim_to_mask"] = True
        self.kwargs["trim_to_visible"] = False
        self.export_psd()

    def export_psd_trim_both(self):
        
        #self.kwargs["ignore_invisible"] = True
        self.kwargs["trim_layers"] = True
        self.kwargs["trim_to_mask"] = True
        self.kwargs["trim_to_visible"] = False
        self.export_psd()

    def export_psd_trim_visible(self):
       
        #self.kwargs["ignore_invisible"] = True
        self.kwargs["trim_layers"] = False
        self.kwargs["trim_to_mask"] = False
        self.kwargs["trim_to_visible"] = True
        self.export_psd()

        
    def show_tree(self):
        """Function to count psd layers and folders"""

        #use self.kwargs to access the psd file
        psd, psd_name = self.kwargs["file"].values()

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

        #Hide layer count button until we open another file.
        #self.tree_button.pack_forget()
        
        
def main():
    # create the root window
    root = tk.Tk()
    w=500
    h=400
    app = App(root,f"{w}x{h}+400+300")


    # run the application
    root.mainloop()

if __name__ == "__main__":
    main()

