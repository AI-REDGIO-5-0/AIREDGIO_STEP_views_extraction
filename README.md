# Views extractor from STEP files

This repository contains a python script to automate the extraction of STEP file’s orthogonal projections using tools available on PythonOCC (Paviot, T. (2022). "pythonocc". Zenodo. https://doi.org/10.5281/zenodo.3605364).

Instructions for use:

1. Download the file ‘views_and_bounding_box_extraction.py’.

2. Fill out the paths for the script execution: `folder_path` is the location containing all the STEP files to be processed, `output_folder_path` is the output directory where the script will save the extracted views, and `save_path` is where the script will save the dataset containing the dimensions of all the objects.

3. Set the desired width and height of output images.

4. Use `setted_tol` to optionally specify a tolerance for the computation of the bounding boxes around objects.

Execute the script.

Six view images (top, bottom, right, left, front, back) will be generated in the chosen folder. The dimensions dataset will be saved in the specified `save_path` directory. 
