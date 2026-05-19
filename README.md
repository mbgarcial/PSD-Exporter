## PSD Layers to PNG batch-exporter
### CS50P Final Project
#### Video Demo: <URL HERE>

### About the project
I created this little app out of a need to streamline the creation of individual PNG files out of the Layers in a PSD file.
I'm a digital illustrator that often works creating 2D graphic assets for videogames, and these assets have mix-and-match elements to create a number of different images to be used in a game.

For example, let's say I have a character. In the PSD File, much like a Dress Up Paper Doll, I have a base body Layer, several layers with different outfits (all inside a folder named 'outfits'), and several layers with different facial expressions (all inside a folder named "expressions"). I could go even further, and separate the outfits into combinable pieces, and the facial expressions into different combinable eyebrows, eyes and mouth.

My needs were:
- Export individual layers and preserve the PSD folder structure in the exported files.
- Include or exclude specific layers or folders to export.
- "Flatten" specified folders, exporting all the contents as one layer.
- Ignore invisivle layers as needed.
- Specify if I wanted the "canvas size" of the transparent pixels around the image cropped, or not, and/or input a specific crop size.
- No need to rename layers to be able to save each inside folders. (When you have dozens of files and dozens of layers each, it gets very time consuming)

I create files using a third party illustration program that creates PSD files, that lacks batch exporting capabilities. Photoshop(paid) and Photopea(free) have some capabilities, but were lacking in what I needed specifically. So, I wondered if I could automate the issue.

### Creation process
The first step was to find a library that could work with PSD files. I found **psd-tools**, which had most of the functionality I wanted out of the box: it could read the file structure of the psd, export layers individually using **pillow**, and it retrieved layer properties like visibility, so I could use that to filter.
Initially, I made the whole thing run very rudimentarily on the console, however I soon realized I needed to visualize the layer structure and ideally make ample use of checkboxes to determine what I wanted and how I wanted to export the layers, instead of relying on commands.
For this, I learned the basics of **tkinter** and created a simple user interface.

The app initially only had the capability to showcase a thumbmnail, by either retrieving an existing thumbnail information from the file or creating a small composited image, then, since psd-tools lacked a function to display the layer tree structure, I created one that returned a representation as text with simple emoji symbols.
The first test was to iterate over all the layers and export them all individually, then to create inclusion or exclusion conditions as filters, then expanded on cropping, resizing, and flattening folders.

### Files and functionality
- **project.py**: The app.
It contains the **App class**, that generates the tkinter application, with all its components and variables. It also has a dictionary inside that stores all the choices the user makes and inputs, so it can transfer it to the exporting function later. Inside it, there are a number of methods that update interdependent fields as needed, and that call external functions to open a PSD file and export its layers when a button is pressed.
This file also contains some base, not inter-dependent helper functions that:
    - Initialize and check the properties that will be required later for exporting the psd layers.
    - Retrieves a thumbnail of the PSD file if it exists and generates a small image composite of it if it doesn't.
    - Create a string representation of a layer to display on the app, and iterate over all the elements of the PSD file to display the tree structure to the user
    - Executes some calculations to return the correct size in pixels of the image, so it can swicth the display from % to pixels when the selection is switched in the Size frame's dropdown menu, and the proportional value on the value not given when aspect ratio is checked.
    - Finds a single layer in the PSD file, to validate the input in "Crop to layer".

- **psd_funcs**: The internal exporting core.
It contains the **ExportableImg class**, which is a container for a layer, folder(group) or a full psd file that will be exported into a PNG image. This class has 4 methods relevant to exporting the image, being ExportableImg.save() the method that actually saves an image into a file, and calls upon the other 3 for parameters to use when doing so.
This file also contains **process_psd()**, which is the function called by the App when the "Export Layers" button is pressed. This iterates over the PSD layers and groups and decides what to do with each (export a layer/folder, skip the layer/folder or flatten a folder) based off the parameters given by the App. Each time it finds a layer or group that needs to be exported, it creatres an ExportableImg and saves it. When it encounters a group that's not going to get merged and saved, it enters it to iterate over its components, remembering its name for filepath saving purposes.
The other functions of the file contain mostly helpers of process_psd() and ExportableImg.save().

### Limitations of the project
I would have liked to have a more visually appealing interface, however tkinter proved to be harder to learn and to design with than I anticipated. In the end, I decided to prioritize working on the project's functionality rather than the aesthetics.
psd-tools has limitations on the kind of layers it's able to work with, so any layers beyond pixel/raster, type and shapes are sadly currently ignored by the application (i.e. adjustments layers). This also applies to layer effects, such as stroke, glow, drop shadow, etc.
Layers in different blending modes are currently untested.
As I discovered psd-tools limitations, I also reported some inconsistencies I found to the developer, and thus I learned how to create an issue report on gitHub, and had the pleasure to have them solved and updated in the library in a timely fashion. 
I would have loved to implement more features, but the whole thing started to be plagued by feature-creep, so I had to cut back.



