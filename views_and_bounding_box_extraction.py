# %% [markdown]
# # AI REDGIO 5.0 - views and bounding box extraction from STEP (.stp) files 

# %% [markdown]
# Information that have to be extracted from the file:  
# - Bounding box (with a customizable tolerance) 
# - Overall object's dimensions
# - Views (along the triedron)

# %% [markdown]
# 1. Set the path to the folder that contains all the files of interest (folder_path ), the one of the folder in which the output views will be saved (output_folder_path ) and the one in which the dataset containing the dimensions and the bounding box dimensions of each dataset will be saved (save_path).

# %%
folder_path = "" #path of the folder that contains the STEP files
output_folder_path = "" #path in which the extracted views will be seved for all the files
save_path = "" #path in which the dataset containing the dimensions of all the files will be saved 

# %% [markdown]
# 2. Set the desired width and height of output images

# %%
screen_width = 3060 
screen_hight = 3060

# %% [markdown]
# 3. Set the tolerance (in mm) that will be used to obtain the bounding box 

# %%
setted_tol = 10

# %% [markdown]
# 4. Run all after having set the required parameters 

# %%
import os
import pandas as pd
from OCC.Extend.DataExchange import read_step_file_with_names_colors
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_sRGB, Quantity_NameOfColor
from OCC.Core.Graphic3d import Graphic3d_MaterialAspect, Graphic3d_TypeOfReflection
from OCC.Core.Graphic3d import Graphic3d_NOM_UserDefined
from OCC.Display.OCCViewer import OffscreenRenderer
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Extend.DataExchange import read_step_file_with_names_colors
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound

# %% [markdown]
# Create the dataframe that will contain all the extracted information for each part

# %%
cad_files = os.listdir(folder_path)
cad_projects_names = [file.split('.')[0] for file in cad_files]
#dataFrame with CAD file names as index
df = pd.DataFrame(index=cad_projects_names, columns=['dimension1','dimension2','dimension3', 'bbox_dim1', 'bbox_dim2', 'bbox_dim3', 'bbox_vol']) 

# %% [markdown]
# Extract the views and the dimensions for all the files

# %%
name_list = ['bottom_view.png', 'top_view.png', 'left_view.png', 'right_view.png', 'front_view.png', 'rear_view.png']

# %%
def get_boundingbox(shape, tol=1e-16, use_mesh=True):

    """return the bounding box of the TopoDS_Shape `shape`
    Parameters
    ----------
    shape : TopoDS_Shape or a subclass such as TopoDS_Face
        the shape to compute the bounding box from
    tol: float
        tolerance of the computed boundingbox
    use_mesh : bool
        a flag that tells whether or not the shape has first to be meshed before the bbox
        computation. This produces more accurate results
    """

    bbox = Bnd_Box()

    if use_mesh:
        mesh = BRepMesh_IncrementalMesh()
        mesh.SetParallelDefault(True)
        mesh.SetShape(shape) #input > TopoDS_Shape
        mesh.Perform()
        if not mesh.IsDone():
            raise AssertionError("Mesh not done.")
    brepbndlib.Add(shape, bbox, use_mesh)

    bbox.SetGap(tol)
    
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    return xmin, xmax, ymin, ymax, zmin, zmax, xmax - xmin, ymax - ymin, zmax - zmin

# %%
def refine_mesh(shape, deflection=0.0005):
    """improve mesh quality"""
    mesh = BRepMesh_IncrementalMesh(shape, deflection)
    mesh.Perform()
    return shape

# %%
for i in range(len(cad_files)):
    file_name = cad_files[i]
    project_name = cad_projects_names[i] #name of the project (index of the dataset)
    file_path = os.path.join(folder_path, file_name)

    #create a folder with the name of the part in which save the extracted views, if it doesn't already exist
    output_folder_path_file = f'{output_folder_path}/{project_name}'
    os.makedirs(output_folder_path_file, exist_ok=True)
    os.chdir(output_folder_path_file) #set where the images will be saved 

    ########## VIEWS EXTRACTION
    shapes_labels_colors = read_step_file_with_names_colors(file_path)

    display = OffscreenRenderer(screen_size=(screen_width, screen_hight))
    display.hide_triedron()

    color1 = Quantity_Color(Quantity_NameOfColor.Quantity_NOC_WHITE)
    color2 = Quantity_Color(Quantity_NameOfColor.Quantity_NOC_WHITE)
    display.set_bg_gradient_color(color1, color2, fill_method=2)

    for shpt_lbl_color in shapes_labels_colors:
        label, c = shapes_labels_colors[shpt_lbl_color]

        shape_material = Graphic3d_MaterialAspect(Graphic3d_NOM_UserDefined)
        shape_material.SetReflectionModeOff(Graphic3d_TypeOfReflection.Graphic3d_TOR_EMISSION)
        shape_material.SetReflectionModeOff(Graphic3d_TypeOfReflection.Graphic3d_TOR_SPECULAR)

        shpt_lbl_color = refine_mesh(shpt_lbl_color) #refine mesh 

        display.DisplayShape(
            shpt_lbl_color, 
            color=Quantity_Color(c.Red(), c.Green(), c.Blue(), Quantity_TOC_sRGB),
            material = shape_material,
            dump_image=False,
            update = False
            
        )

    display.GetSelectedShape()

    fct_list = [display.View_Bottom, display.View_Top, display.View_Left, display.View_Right, display.View_Front, display.View_Rear]

    display.Repaint()

    for i in range(len(name_list)):

        fct_list[i]() #select the view

        display.FitAll() #center the solid 

        #save the extracted images in the correct folder 
        display.ExportToImage(image_filename=name_list[i])


    ########### DIMENSIONS and BOUNDING BOX
    
    builder = BRep_Builder()
    compound_shape = TopoDS_Compound()
    builder.MakeCompound(compound_shape)

    #iterate over the shapes in shapes_labels_colors and add them to the compound
    for shape, (label, color) in shapes_labels_colors.items():
        builder.Add(compound_shape, shape)

    #dimensions
    xmin, xmax, ymin, ymax, zmin, zmax, deltax, deltay, deltaz = get_boundingbox(compound_shape) #tol unit of measurement is mm
    df.loc[f'{project_name}', ['dimension1', 'dimension2', 'dimension3']] = [deltax, deltay, deltaz]
    #bbox dimensions
    _, _, _, _, _, _, deltax_bbox, deltay_bbox, deltaz_bbox = get_boundingbox(compound_shape, tol=setted_tol) 
    bbox_vol = deltax_bbox*deltay_bbox*deltaz_bbox
    df.loc[f'{project_name}', ['bbox_dim1', 'bbox_dim2', 'bbox_dim3', 'bbox_vol']] = [deltax_bbox, deltay_bbox, deltaz_bbox, bbox_vol]

# %%
#save the dataset containing the dimensions
df_path = os.path.join(save_path, 'dimensions.csv')
df.to_csv(df_path)


