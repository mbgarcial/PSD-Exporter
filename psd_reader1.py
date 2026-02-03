

from psd_funcs import *
import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog as fd #This is for opening files
from PIL import ImageTk


#TODO:
# - Add progress bar for big files.

#-------------------------------------------------------------------------------------------
# This version has docstrings, optimized func and also reads folders and invisible layers.
#-------------------------------------------------------------------------------------------

class App:
    """Configures and adds widgets to a tk window. Also handles functions that are passed to said widgets."""
    def __init__(self, master, geometry = "500x300+400+300"):
        # Master is the TK window we'll be applying all these to.
        self.master = master
        # Give the window a name
        master.title("Open File testing")

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
        self.right_frame  = tk.LabelFrame(self.frame, text="PSD info", padx=5, width=self.width/2, height=self.height-20)
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
        # Button to count layers and folders, calls self.psdcount
        self.count_button = ttk.Button(self.left_frame, text="Count layers & folders", command=self.psdcount)

        # This is the PSD info text (currently number of layers and number of folders). It's initilized with ""
        self.psdinfo      = tk.Message(self.right_frame, text="", width=self.width/2-10)
        
        # Statusbar at the bottom
        self.status_bar   = tk.Label(self.bottom_frame, text="", bd=1, relief=tk.SUNKEN, anchor=tk.CENTER, width=40)
        
        self.thumbnail = tk.Label(self.left_frame)
        # Pack the widgets.
        # The count_button only gets packed after opening a file.
        self.open_button.pack(expand=True)
        self.psdinfo.pack()
        self.status_bar.pack()

    def select_file(self):
        """Function to open a file file and read it"""
        #filetypes for the tkinter dialogue
        filetypes = (('PSD files', '*.psd'), ('All files', '*.*'))
        #this opens an open file window.
        filename  = fd.askopenfilename(title='Open a psd file', filetypes=filetypes, initialdir=self.lastdir)

        #this is to set the open file starding dir to the path of the last opened file next time it's used.
        match = re.match(r"(.*/).*\.psd",filename)
        if match:
            self.lastdir = match.group(1)

        #if we opened a psd, read it
        if filename:
            result = self.read_psd(filename)
            #if reading the file was successful, assign its result to the app to pass it to other funcs.
            if result:
                self.kwargs = result
        
    def read_psd(self,filename):
        """Function to open a PSD file and read it"""

        #call the external read psd func
        result = read_psd(filename)
        thumb = result["psd"].thumbnail()
        if thumb:
            #thumb.save("thumb.png")
            thumb = ImageTk.PhotoImage(thumb)


        # update text of status bar
        if not result:
            self.status_bar.config(text = "Couldn't read the file")
        else:
            self.status_bar.config(text = "Opened "+ result["psd_name"]) #type:ignore
            # show the thumbnail
            if thumb:
                self.thumbnail.config(image=thumb)
                self.thumbnail.image = thumb #type: ignore
                self.thumbnail.pack(expand = True)
            # reset layercount text
            self.psdinfo.config(text = "")

        #Add button to count layers!
        self.count_button.pack(expand = True)

        # return the result of the read psd func (a dict that's empty if it fails)
        return result
        
    def psdcount(self):
        """Function to count psd layers and folders"""

        #use self.kwargs to access the psd file
        psd, psd_name = self.kwargs.values()

        #update status bar
        self.status_bar.config(text="Counting layers and folders...")
        self.master.update_idletasks()

        #count using external functions
        layers = str(layercount(psd))
        folders = str(foldercount(psd))
        inv_layers, inv_folders = countinvisible(psd)
        #Update status bar
        self.status_bar.config(text="Done!")
        self.master.update_idletasks()

        #Update PSD info
        self.psdinfo.config(text=str(psd_name)+": \n📁"+folders+" folders ("+str(inv_folders)+" invisible)\n📄"+layers+" layers ("+str(inv_layers)+" invisible)")
        #self.psdinfo.config(text=str(psd_name)+": \n"+get_repr(psd))

        #Hide layer count button until we open another file.
        self.count_button.pack_forget()


#------------------------
# Basics that work

def layercount(psd:PSDImage)->int:
    """
    This function counts the number of layers on a PSD object and returns an int. It ignores folders.

    Parameters:
        psd (PSDImage) : A PSDImage object from psd_tools to read the layers from.
    
    Raises:
        ValueError: if no PSD is given.
    
    Returns:
        int: the number of layers the PSD has. It ignores folders.

    """
    if not psd:
        raise ValueError("PSD is empty")
    
    # using a sum and a generator rather than a for loop with a counter!
    # loop through all psd items and count them if they're not folders
    return sum(1 for layer in psd.descendants() if not layer.is_group()) 
    

def countinvisible(psd:PSDImage)->tuple:
    """Counts invisible layers and folders. Returns a tuple."""
    if not psd:
        raise ValueError("PSD is empty")
    
    layers,folders = 0,0
    # loop through all psd items and count thm if not folders
    layers  = sum(1 for layer in psd.descendants() if not layer.is_group() and not layer.visible) 
    folders = sum(1 for layer in psd.descendants() if layer.is_group() and not layer.visible) 
    return (layers,folders)


def foldercount(psd:PSDImage)->int:
    """
    This function counts the number of folders on a PSD object and returns an int.

    Parameters:
        psd (PSDImage) : A PSDImage object from psd_tools to read the folders from.
    
    Raises:
        ValueError: if no PSD is given.
    
    Returns:
        int: the number of folders the PSD has.

    """
    if not psd:
        raise ValueError("PSD is empty")
    # loop through all psd items and count them if folders
    return sum(1 for layer in psd.descendants() if layer.is_group())
    

def folderlist(psd:PSDImage)->list:
    """
    This function returns a list of folder names.

    Parameters:
        psd (PSDImage) : A PSDImage object from psd_tools to read the folders from.
    
    Raises:
        ValueError: if no PSD is given.
    
    Returns:
        list: the names of the folders the PSD has.

    """
    if not psd:
        raise ValueError("PSD is empty")
    # loop through all psd items and add their name to list if folders
    return [layer.name for layer in psd.descendants() if layer.is_group()]
    

def layerlist(psd:PSDImage)->list:
    """
    This function returns a list of layer names.

    Parameters:
        psd (PSDImage) : A PSDImage object from psd_tools to read the folders from.
    
    Raises:
        ValueError: if no PSD is given.
    
    Returns:
        list: the names of the layers the PSD has, excluding folders

    """
    if not psd:
        raise ValueError("PSD is empty")
    # loop through all psd items and add their name to list if not folder
    return [layer.name for layer in psd.descendants() if not layer.is_group()]
    

        
        
def main():
    # create the root window
    root = tk.Tk()
    w=500
    h=300
    app = App(root,f"{w}x{h}+400+300")


    # run the application
    root.mainloop()

if __name__ == "__main__":
    main()

