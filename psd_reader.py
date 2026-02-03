from psd_tools import PSDImage
import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog as fd #This is for opening files
import re

#TODO:
# - Add progress bar for big files.

# This function counts the number of layers on a PSD object and returns an int. It ignores folders.
# it also takes none, and returns 0 in that case.
def layercount(psd:PSDImage|None)->int:
    if not psd:
        return 0
        #maybe raise an error here?
    else:
        count = 0
        for layer in psd.descendants():
            if not layer.is_group():
                count+=1
            else:
                pass
        return count

#This function counts folders.
def foldercount(psd:PSDImage|None)->int:
    if not psd:
        return 0
        #maybe raise an error here?
    else:
        count = 0
        for layer in psd.descendants():
            if layer.is_group():
                count+=1
            else:
                pass
        return count
    

# This function opens the PSD and returns a dict with the psd object and its name (filename.psd)
def read_psd(filename)-> dict:
    psd_dict = dict()
    try:
        psd_dict["psd"] = PSDImage.open(filename)
        
    except:
        return {}

    match = re.match(r".*/(.*\.psd)",filename)
    
    if match:
        psd_dict["psd_name"] = match.group(1)

    return psd_dict


class App:
    def __init__(self, master, geometry = "500x300"):
        # Master is the TK window we'll be applying all these to.
        self.master = master
        # Give the window a name
        master.title("Open File testing")
        # Size.
        master.geometry(geometry)

        # These are to pass stuff around the gui and the external function
        self.args = list()
        self.kwargs = dict()

        # These are frames to put widgets into. A frame that fills the indow, then another one at the bottom.
        self.frame = tk.Frame(master, pady=10)
        self.frame.pack()
        self.bottomframe =tk.Frame(master)
        self.bottomframe.pack(side=tk.BOTTOM)

        # open file button, calls select_file
        self.open_button = ttk.Button(self.frame, text='Open PSD', command=self.select_file)
        # count layers and folders button, calls psd.count
        self.count_button =ttk.Button(self.frame,text="Count layers & folders",command=self.psdcount)

        self.psdinfo=tk.Label(self.frame, text="")
        
        # Statusbar
        self.status_bar = tk.Label(
            self.bottomframe, 
            text="", 
            bd=1, 
            relief=tk.SUNKEN,
            anchor=tk.CENTER, 
            width=40
            )
        
        self.open_button.pack(expand=True)
        self.psdinfo.pack()
        self.status_bar.pack()

    def select_file(self):
        filetypes = (
            ('PSD files', '*.psd'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=filetypes)
        
        result = self.read_psd(filename)
        if result:
            self.kwargs = result
        

    def read_psd(self,filename):
        result = read_psd(filename)
        if not result:
            self.status_bar.config(text= "Couldn't read the file")
        else:
            self.status_bar.config(text="Opened "+result["psd_name"]) #type:ignore
            #reset layercount text
            self.psdinfo.config(text="")


        #Add button to count layers!
        self.count_button.pack(expand=True)
        return result
        
    def psdcount(self):
        
        psd, psd_name = self.kwargs.values()
        self.status_bar.config(text="Counting layers and folders...")
        self.master.update_idletasks()
        layers = str(layercount(psd))
        folders = str(foldercount(psd))
        #print(layers,folders)
        self.status_bar.config(text="Done!")
        self.master.update_idletasks()
        self.psdinfo.config(text=str(psd_name)+" has\n"+layers+" layers and "+folders+" folders")
        self.count_button.pack_forget()
        
        


# create the root window
root = tk.Tk()
app = App(root,'300x150')


# run the application
root.mainloop()

