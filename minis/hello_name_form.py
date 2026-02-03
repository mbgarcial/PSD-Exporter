#testing GUI stuff!
import tkinter as tk

# declaring string variable
# for storing names

class App:
    def __init__(self, master, geometry = "500x300"):
        self.master = master
        master.title("My GUI Test App")
        master.geometry(geometry)

        """Add widgets here"""

        self.status_bar = tk.Label(master, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.button = tk.Button(master, text="Perform Action", command=self.perform_action)
        self.button.pack(pady=10)

    def perform_action(self):
        self.update_status("Exporting...")
        # Simulate some work
        self.master.after(2000, lambda: self.update_status("Done exporting!"))

    def update_status(self, message):
        self.status_bar.config(text=message)
        
    


        
#-------------
#Create a new window and give it a name.
app = tk.Tk()

#This sets up the whole thing :O
#app = App(root)
#root.mainloop()

first_var = tk.StringVar()
last_var  = tk.StringVar()

def submit():

    first = first_var.get()
    last  = last_var.get()
    if first == last and first == "":
        status_bar.config(text="Please input your name")
        
    else:
        status_bar.config(text="Hello, "+first+" "+last+"!")
    
        first_var.set("")
        last_var.set("")


#Main frame
frame = tk.Frame(app, pady=10)
frame.pack()

#Bottom frame
bottomframe = tk.Frame(app)
bottomframe.pack( side = tk.BOTTOM )


#Grid
tk.Label(frame, text='First Name').grid(row=0)
tk.Label(frame, text='Last Name').grid(row=1)
e1 = tk.Entry(frame, textvariable = first_var)
e2 = tk.Entry(frame, textvariable = last_var)
# creating a button using the widget 
# Button that will call the submit function 
sub_btn=tk.Button(frame, text = 'Submit', command = submit)


e1.grid(row=0, column=1)
e2.grid(row=1, column=1)
sub_btn.grid(row=2, column=0)

status_bar = tk.Label(bottomframe, text="Please input your name!", bd=1, relief=tk.SUNKEN, anchor=tk.CENTER, width=40)

# # A button that closes terminates the program
status_bar.pack()
button = tk.Button(bottomframe, text='Exit', command=app.destroy)


# #Pack the widgets
button.pack(side = tk.BOTTOM, pady=10)
app.mainloop()



