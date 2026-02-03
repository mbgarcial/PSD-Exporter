#testing ttk.treeview
import tkinter as tk
from tkinter import ttk

#-------------------------
# Functions that may be useful for tree showing with ttk.Treeview...?
#-------------------------

def main():

    root = tk.Tk()
    root.title("Tkinter Treeview")
 

    # TUTORIAL AT:
    # https://recursospython.com/guias-y-manuales/vista-de-arbol-treeview-en-tkinter/

    # Create treeview
    treeview = ttk.Treeview(root, style= "Custom.Treeview", show="tree")
    #-------
    # ADD ELEMENTS HERE
    # treeview expects a parent (in this case a "" for no parent, an index (or "end"), a unique id (optional), and other options.)
    # Now we assign this as a node...?
    item = treeview.insert("", tk.END, text="Element 1", iid="elem01")
    # and insert an element that has item as parent
    subitem = treeview.insert(item, tk.END, text="Subelement 1", iid="elem01-subelem01")
    treeview.insert(subitem, tk.END, text="Another element", iid="subelem01-anotherelem")
    item2 = treeview.insert("", tk.END, text="Element 2", iid="elem02")


    item_info = treeview.item("elem01") #this returns a dict of properties
    treeview.item("elem01",text="Element 01, altered!") #this changes a property of the item. can do it with a func.
    item_children = treeview.get_children(item) #a tuple with the iids of all item's children (but not their subchildren)
    tree_children = treeview.get_children() # same as above, but for root level elements
    #treeview.move(item, item2, tk.END) #this moves an element to another parent
    # Elimina el elemento 2.
    treeview.delete(item2)
    # Desvincula el elemento 1.
    #treeview.detach(item)
    
    print(treeview.exists(item2)) #bool if item exists in tree
    print(treeview.exists("elem02")) #should be the same as above

    
    #-----------
    treeview.pack()

    root.mainloop()




if __name__ == "__main__":
    main()