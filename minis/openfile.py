#This opens a file.
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd



class App:
    def __init__(self, master, geometry = "500x300"):
        self.master = master
        master.title("Open File testing")
        master.resizable(False, False)
        master.geometry(geometry)

        # open button
        self.open_button = ttk.Button(
            root,
            text='Open a File',
            command=self.select_file
        )
        self.status_bar = tk.Label(
            root, 
            text="", 
            bd=1, 
            relief=tk.SUNKEN,
            anchor=tk.CENTER, 
            width=40
            )
        self.open_button.pack(expand=True)
        self.status_bar.pack()

    def select_file(self):
        filetypes = (
            ('TXT files', '*.txt'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=filetypes)

        self.status_bar.config(text=self.read_txt(filename))
        #print(filename)
        
    def read_txt(self,filename):
        with open(filename,"r") as file:
            return file.readline().strip()

# create the root window
root = tk.Tk()
app = App(root,'300x150')


# run the application
root.mainloop()