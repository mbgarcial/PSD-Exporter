

from psd_funcs import *
import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog as fd #This is for opening files
import tkinter.scrolledtext as scrolledtext
from PIL import ImageTk
#from pathlib import Path


#TODO:
# - Add progress bar for big files.

#-------------------------------------------------------------------------------------------
# This version shows non-expandable tree on opening, and has buttons to export a flat PSD or layers.
# Default behavior is:
#       - export layers trimmed of blank pixels
#       - ignore invisible layers
#       - ignore clipping layers and apply them to layers that have them
#       - apply masks to layers (NOT GROUPS) that have them
#       - create new folders for groups and export their contents
#       - if a group has a mask, apply it to all its children.
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
        master.title("Export Layers (some no longer work as intented)")

        # Size
        master.geometry(geometry)
        self.width  = int(geometry.split("x", 1)[0])
        self.height = int(geometry.split("x", 1)[1].split("+")[0])

        # These are to pass stuff around the gui and the external function
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

        # Export PSD button, exports PSD (flat)
        self.export_button = ttk.Button(self.left_frame, text='Export flattened PSD',command=self.export_psd)
        
        # Export PSD button, exports PSD layers (root only)
        self.export_layers_button = ttk.Button(self.left_frame, text='Export root PSD layers',command=self.export_psd_layers)
        
        # Export PSD button, exports PSD layers (root and folders - ignore invisible)
        self.export_folders_button = ttk.Button(self.left_frame, text='Export layers to folders (ignore invisible)',command=self.export_psd_folders)

        # Export PSD button, exports PSD layers (root and folders - don't ignore invisible)
        self.export_invisibles_button = ttk.Button(self.left_frame, text='Export(...) (not ignore invisible)',command=self.export_psd_folders_invisible)

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
            self.export_button.pack(expand=True)
            self.export_layers_button.pack(expand=True)
            self.export_folders_button.pack(expand=True)
            self.export_invisibles_button.pack(expand=True)


        # return the result of the read psd func (a dict that's empty if it fails)
        return result
    
    def export_psd(self, layers=False, folders=False):
        """Function that calls other exporter functions, for the PSDImage file"""
        # use self.kwargs to access the psd file
        psd, psd_name = self.kwargs["file"].values()
        ext = self.kwargs.get("extension",".png")

        invisignore = self.kwargs.get("ignore_invisible", True)

        # get the name of the psd.
        name = psd_name.removesuffix(".psd")

        # Make a path for the new folder where we'll be saving things
        # path = self.lastdir+"/"+name

        # filetypes for the tkinter dialogue
        filetypes = [('PNG', '*.png'), ('JPG', '*.jpg'), ('All files', '*.*')]

        # this opens a save_as window.
        path  = fd.askdirectory(title = 'Choose where to save', initialdir = self.lastdir)

        # if user cancels
        if not path:
            return

        # Call external save function
        if not layers:
            print("exporting flattened psd!")
            result = process_psd(psd, name, path, ext=ext, flat = True)
        else:
            print("exporting layers inside folders!")
            result = process_psd(psd, name, path, ext=ext, ignore_invisible = invisignore)

        
        # update status bar
        if result == True:
            self.status_bar.config(text="Exported "+psd_name+" at "+path+"/" )
            
        else:
            self.status_bar.config(text=result)
        
        self.master.update_idletasks()

    def export_psd_layers(self):
        """Calls export_psd with layers = True"""
        self.export_psd(layers=True)

    def export_psd_folders(self):
        """Calls export_psd with folders = True"""
        self.kwargs["ignore_invisible"] = True
        self.export_psd(folders=True, layers=True)

    def export_psd_folders_invisible(self):
        """Calls export_psd with folders = True"""
        self.kwargs["ignore_invisible"] = False
        self.export_psd(folders=True, layers=True)

        
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

