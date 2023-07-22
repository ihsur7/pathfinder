# Command Line Interface for Pathfinder
# Author: Rushabh Patel
# Date: 2023-07-22
# Version: 1.0

import sys
import os
import numpy as np
import trimesh
import PVGeo as pg
import warnings
import math
import mdutils as mu
import pypandoc

import plotter
import dijkstra as dj

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import pyvista as pv

def coord_array(arr):
    """
    Converts a 3D array of coordinates into a more readable format.

    Parameters:
        arr (np.ndarray): A 3D NumPy array representing the voxelized points.

    Returns:
        np.ndarray: A 2D NumPy array containing the coordinates (x, y, z) of the non-zero elements in the input array.
    """
    coord = np.asarray(np.where(arr))
    coords = np.empty((len(coord[0]),3), dtype=np.int64)
    for i in np.arange(len(coord[0])):
        coords[i][0:3] = coord[:,i]
    return coords

def calculate_direction_changes(paths):
    
    """
    Calculates the number of direction changes (e.g., changes in movement direction) in each path of the given list of paths.

    Parameters:
        paths (list): A list of paths, where each path is represented as a list of coordinates (x, y, z).

    Returns:
        tuple: A tuple containing two lists. The first list contains the number of direction changes for each path,
               and the second list contains the indices of the direction changes for each path.
    """
    def calculate_unit_vector_array(arr):
        varr = np.zeros((len(arr) - 1, 3), dtype=int)
        for i in range(len(varr)):
            varr[i] = np.subtract(arr[i + 1], arr[i])
        return varr
    
    def count_direction_changes(varr):
        """
        Counts the number of direction changes in a given path represented by a vector array.

        Parameters:
            varr (np.ndarray): A 2D NumPy array representing the vector array of a path.

        Returns:
            tuple: A tuple containing the total number of direction changes in the path and a list of indices
                where the direction changes occur.
        """
        # Note: If the input paths list is empty, the function will return empty lists for direction changes and indices.
        dir_change = 0
        dir_change_ind = []
        for i in range(1, len(varr)):
            if not np.array_equal(varr[i], varr[i - 1]):
                dir_change += 1
                dir_change_ind.append(i)
        return dir_change, dir_change_ind
    all_dir_changes = []
    all_dir_change_inds = []
    for path in paths:
        varr = calculate_unit_vector_array(path)
        dir_change, dir_change_ind = count_direction_changes(varr)
        all_dir_changes.append(dir_change)
        all_dir_change_inds.append(dir_change_ind)
    return all_dir_changes, all_dir_change_inds

def joints_calc(all_dir_changes, all_dir_change_inds, paths, input_loc, output_loc, p):
    """
    Calculates the number of L joints, T joints, and piping segments based on the direction change data and input/output locations.

    Parameters:
        all_dir_changes (list): A list containing the number of direction changes for each path.
        all_dir_change_inds (list): A list of lists, where each sublist contains the indices of direction changes for each path.
        paths (list): A list of paths, where each path is represented as a list of coordinates (x, y, z).
        input_loc (np.ndarray): A 1D NumPy array representing the input coordinates (x, y, z).
        output_loc (list): A list of 1D NumPy arrays, where each array represents the output coordinates (x, y, z) for a path.
        p (np.ndarray): A 3D NumPy array representing the voxel grid.

    Returns:
        tuple: A tuple containing the number of L joints, T joints, and piping segments.
    """
    #only works for 2 paths
    #assumes endpoints are L_joints
    #assumes only 1 input and n outputs
    L_joint = 1+ len(output_loc)
    T_joint = 0
    Piping = 0
    if len(paths) > 2:
        print('Error: More than 2 paths. Cannot calculate joints.')

    if len(paths) == 2:
        ind1 = all_dir_change_inds[0]
        ind2 = all_dir_change_inds[1]
        p1 = paths[0]
        p2 = paths[1]
        for x,y in zip(ind1, ind2):
            coord1_curr = p1[x]
            coord1_prev = p1[x-1]
            coord1_next = p1[x+1]
            coord2_curr = p2[y]
            coord2_prev = p2[y-1]
            coord2_next = p2[y+1]
            if coord1_prev == coord2_prev and coord1_next == coord2_next:
                print('Common L_joint', p1[x])
                L_joint += 1
            elif coord1_prev == coord2_prev and coord1_next != coord2_next:
                print('Divering T_joint', p1[x])
                T_joint += 1
            elif coord1_prev != coord2_prev and coord1_next == coord2_next:
                print('Converging T_joint', p1[x])
                T_joint += 1
            elif coord1_prev != coord2_prev and coord1_next != coord2_next:
                if coord1_curr == coord2_curr:
                    print('Unknown X_joint', p1[x])
                else:
                    print('Independent L_joint', p1[x], p2[y])
                    L_joint += 2
            else:
                print('Error')
        Piping = np.count_nonzero(p == -1) - L_joint - T_joint
    elif len(paths) == 1:
        L_joint += len(all_dir_change_inds[0])
        Piping = len(paths[0]) - L_joint
    return L_joint, T_joint, Piping

def load_file(filepath, res=0.05):
    """
    Loads an STL file, voxelizes it, and returns the voxelized points, voxel grid, and voxel size.

    Parameters:
        filepath (str): The file path of the STL file to load.
        res (float, optional): The resolution for voxelization (default is 0.05).

    Returns:
        tuple: A tuple containing the voxelized points (vx), point cloud data (pts), voxel grid, and voxel size (voxel_size).
    """
    # Note: Currently, only STL files are supported for loading.
    if os.path.exists(filepath):
        global vx, pts, voxel_grid
        stl_file = trimesh.load_mesh(fp, enable_postprocessing=True, solid=True)
        voxelized = stl_file.voxelized(res)
        voxel_grid_trimesh = voxelized.matrix
        voxel_grid = np.array(voxel_grid_trimesh, dtype=np.int64)
        stl_file.vertices = stl_file.vertices*304.8
        voxel_size = stl_file.bounds[1][1]/voxel_grid.shape[1] #mm per voxel
        voxel_grid = np.pad(voxel_grid, 3, 'constant', constant_values=0)
        coords = coord_array(voxel_grid)
        pts = pv.PolyData(coords, force_float=False)
        vx = pg.filters.VoxelizePoints().apply(pts)
        return vx, pts, voxel_grid, voxel_size

def assign_input_loc(input_loc):
    """
    Assigns the input coordinates globally for later use.

    Parameters:
        input_loc (np.ndarray): A 1D NumPy array representing the input coordinates (x, y, z).
    """
    global inp_loc
    inp_loc = input_loc

def assign_output_loc(output_loc):
    """
    Assigns the output coordinates globally for later use.

    Parameters:
        output_loc (list): A list of 1D NumPy arrays, where each array represents the output coordinates (x, y, z) for a path.
    """
    global out_loc
    out_loc = output_loc

class pPlotter:
    """
    A class to provide plotting functionality for the voxelized points and the point cloud data.

    Attributes:
        vx (pv.PolyData): Voxelized points as a PyVista PolyData object.
        pts (pv.PolyData): Point cloud data as a PyVista PolyData object.

    Methods:
        __init__(self, vx, pts): Initializes the pPlotter class with voxelized points and point cloud data.
        plot(self): Plots the voxelized points and point cloud data using the plotter.Plotter class.
    """
    def __init__(self, vx, pts):
        self.vx = vx
        self.pts = pts
        self.p = plotter.Plotter(self.vx, self.pts)
    
    def plot(self):
        self.p = plotter.Plotter(vx, pts).plot()

def set_o(o):
    """
    Sets the output coordinates based on the provided input.

    Parameters:
        o (list or np.ndarray): A list or a 1D NumPy array representing the output coordinates (x, y, z).

    Returns:
        np.ndarray: A 2D NumPy array containing the output coordinates (x, y, z).
    """
    if len(o) >= 3:
        out_loc = np.reshape(o, (len(o)//3, 3)).astype(np.int64)
    else:
        out_loc = [np.array(o, dtype=np.int64)]
    assign_output_loc(out_loc)
    return out_loc

def set_i(i):
    """
    Sets the input coordinates based on the provided input.

    Parameters:
        i (list or np.ndarray): A list or a 1D NumPy array representing the input coordinates (x, y, z).

    Returns:
        np.ndarray: A 1D NumPy array containing the input coordinates (x, y, z).
    """
    inp_loc = np.array(i, dtype=np.int64)
    assign_input_loc(inp_loc)
    return inp_loc

def results(l_joints, t_joints, pipe_segments, pipe_length, std_length):
    """
    Creates and returns a dictionary containing the results of the pipeline calculation.

    Parameters:
        l_joints (int): Number of L joints in the pipeline.
        t_joints (int): Number of T joints in the pipeline.
        pipe_segments (int): Number of pipe segments in the pipeline.
        pipe_length (float): Total length of pipe required for the pipeline.
        std_length (float or None): Standard length of pipe (optional).

    Returns:
        dict: A dictionary containing the results with keys - 'L Joints', 'T Joints', 'Pipe Segments', 'Pipe Length', 'Standard Length'.
    """
    global mydict
    mydict = {'L Joints': l_joints, 'T Joints': t_joints, 'Pipe Segments': pipe_segments, 'Pipe Length': pipe_length, 'Standard Length': std_length}
    return mydict

def setres(r):
    """
    Sets the resolution for voxelization.

    Parameters:
        r (float): The resolution for voxelization.
    """
    global res
    res = r

def start_plotter(fl):
    """
    Starts the plotter.Plotter class for the voxelized points and point cloud data to enable face picking.
    """
    global fl_plot
    fl_plot = plotter.Plotter(fl[0], fl[1], grid=True, axes=True)
    return fl_plot


if __name__ == "__main__":
    # Code for the command-line interface (CLI) starts here.
    global fl_plot, folder
    print()
    print("Pathfinder CLI")
    print()
    print("Type 'help' for a list of commands")
    print()
    inp_loc = None
    inp_loc = None
    assign_input_loc(inp_loc)
    assign_output_loc(inp_loc)
    while True:
        command = input("Enter command: ")
        if command == ' ' or command == '':
            # Ignore empty commands and spaces.
            continue
        elif command == "setres":
            # Command to set the resolution for voxelization.
            res = input("Enter resolution: ")
            if res is None:
                print("No resolution entered. Recommended resolution is 0.05.")
            else:
                try:
                    res = float(res)
                    assert 1 > res > 0, "Invalid resolution."
                except AssertionError as e:
                    print(e)
                setres(res)
        elif command == "loadmodel":
            # Command to load a 3D model from an STL file and voxelize it.
            fp = input("Enter filepath: ")
            if os.path.exists(fp):
                folder = os.path.dirname(fp)
                fl = load_file(fp)
                start_plotter(fl)
            else:
                print("File does not exist")
        elif command == "pickio":
            # Command to interactively pick input and output coordinates from the loaded model.
            try:
                if fl is None:
                    print("No file loaded")
            except NameError:
                print("No file loaded")
                continue
            pplot = start_plotter(fl).plot()
            try:
                set_i(fl_plot.get_i())
                set_o(fl_plot.get_o())
            except TypeError:
                print("No input and output coordinates selected.")
        elif command == "setinput":
            # Command to manually set the input coordinates (x, y, z).
            si = input("Enter input coordinates (x,y,z): ")
            if si is None:
                print("No input coordinates entered")
            else:
                try:
                    inp = si.split(",")
                    inp = [int(i) for i in inp]
                    assert len(inp) == 3, "Invalid number of input coordinates."
                    assert all([isinstance(item, int) for item in inp]), "Invalid input coordinates."
                except AssertionError as e:
                    print(e)
                    continue
                set_i(inp)
        elif command == "setoutput":
            # Command to manually set the output coordinates (x, y, z).
            so = input("Enter output coordinates (x1,y1,z1,...): ")
            if so is None:
                print("No output coordinates entered")
            else:
                try:
                    out = so.split(",")
                    out = [int(i) for i in out]
                    assert len(out)%3 == 0, "Invalid number of input coordinates. Must be multiple of 3."
                    assert all([isinstance(item, int) for item in out]), "Invalid input coordinates."
                except AssertionError as e:
                    print(e)
                    continue
                set_o(out)
        elif command == "standardlength":
            # Command to set the standard length of the pipe for calculations.
            sl = input("Enter standard length of pipe (mm): ")
            if sl is None:
                print("No standard length entered")
            else:
                try:
                    assert sl.isnumeric(), "Invalid standard length."
                    sl = float(sl)
                    assert sl > 0, "Invalid standard length."
                except AssertionError as e:
                    print(e)
                    continue
                print(f"Standard length set to {sl} mm")
        elif command == "run":
            # Command to run the dijkstra algorithm and calculate the shortest path and joints.
            if inp_loc is None:
                print("No input coordinates entered")
            elif out_loc is None:
                print("No output coordinates entered")
            else:
                print("Running...")
                paths = []
                if fl[2][inp_loc[0], inp_loc[1], inp_loc[2]] == 1:
                    print("Input location is in obstacle. Please select another input location.")
                    continue
                for i in range(len(out_loc)):
                    if fl[2][out_loc[i][0], out_loc[i][1], out_loc[i][2]] == 1:
                        print(f"Output location {i+1} is in obstacle. Please select another output location.")
                        continue
                p = np.zeros(shape=fl[2].shape)
                for i in range(len(out_loc)):
                    path = dj.dijkstra(inp_loc, out_loc[i], fl[2])
                    for i in range(len(path)):
                        p[path[i][0], path[i][1], path[i][2]] = -1
                    paths.append(path)
                for i in range(fl[2].shape[0]):
                    for j in range(fl[2].shape[1]):
                        for k in range(fl[2].shape[2]):
                            fl[2][i,j,k] += p[i,j,k]
                all_dir_changes, all_dir_change_inds = calculate_direction_changes(paths)
                for i, (dir_change, dir_change_ind) in enumerate(zip(all_dir_changes, all_dir_change_inds)):
                    print(f"Path {i+1}:")
                    print("Direction Changes:", dir_change)
                    print()
                joints = joints_calc(all_dir_changes, all_dir_change_inds, paths, inp_loc, out_loc, p)
                print("Number of L joints:", joints[0])
                print("Number of T joints:", joints[1])
                print("Number of Pipe Segments:", joints[2])
                print(f"Length of Pipe Required: {joints[2]*fl[3]:.2f} mm")
                try:
                    if sl is not None:
                        print(f"Number of Standard Lengths: {math.ceil(joints[2]*fl[3]/sl):.2f}")
                except NameError:
                    print("Standard length not set")
                    print(f"Length of Pipe to Purchase: {math.ceil(joints[2]*fl[3]/10)*10:.2f} mm")
                coords = coord_array(fl[2])
                pts = pv.PolyData(coords, force_float=False)
                vx = pg.filters.VoxelizePoints().apply(pts)
                flat = fl[2].flatten()
                flat = flat[flat != 0]
                plot = plotter.Plotter(vx, pts, flat = flat, picker=False, grid = False, axes = False).plot()
                global img_plot_pts, img_plot_vx, img_plot_flat
                img_plot_pts = pts
                img_plot_vx = vx
                img_plot_flat = flat
                try:
                    if sl is not None:
                        results(joints[0], joints[1], joints[2], joints[2]*fl[3], sl)
                except NameError:
                    results(joints[0], joints[1], joints[2], joints[2]*fl[3], None)
                print("Done")
        elif command == "generatereport":
            # Command to generate a report with results and images of the pipeline.
            if not os.path.exists(f'{folder}/temp'):
                    os.makedirs(f'{folder}/temp')
            assert img_plot_pts is not None, "No data to generate images for report."
            img_plot = pv.Plotter(off_screen=True)
            img_plot.add_mesh(img_plot_vx, color=True, show_edges=True, scalars = img_plot_flat, cmap=['red', 'gray'], opacity=1)
            img_plot.enable_parallel_projection()
            img_plot.remove_scalar_bar()
            cpos = ['top', 'top_right_iso', 'front', 'right', 'bottom', 'bottom_right_iso']
            for i in range(len(cpos)):
                img_plot.camera_position = 'yz'
                if cpos[i] == 'front':
                    img_plot.camera.elevation = 0
                    img_plot.camera.azimuth = 0
                    img_plot.render()
                elif cpos[i] == 'top':
                    img_plot.camera.elevation = 90
                    img_plot.camera.azimuth = 0
                    img_plot.render()
                elif cpos[i] == 'right':
                    img_plot.camera.elevation = 0
                    img_plot.camera.azimuth = 90
                    img_plot.render()
                elif cpos[i] == 'top_right_iso':
                    img_plot.camera.elevation = 45
                    img_plot.camera.azimuth = 45
                    img_plot.render()
                elif cpos[i] == 'bottom':
                    img_plot.camera.elevation = -90
                    img_plot.camera.azimuth = 0
                    img_plot.render()
                elif cpos[i] == 'bottom_right_iso':
                    img_plot.camera.elevation = -45
                    img_plot.camera.azimuth = 45
                    img_plot.render()
                img_plot.screenshot(f'{folder}/temp/{cpos[i]}.png', transparent_background=True)
            mdfile = mu.MdUtils(file_name='report.md', title='Pipeline Report')
            mdfile.new_header(level=1, title='Overview')
            mdfile.new_paragraph('This is a report generated by the Pathfinder CLI. It contains the results shortest path between input and output points using the Dijkstra algorithm and the images of the pipeline.')
            mdfile.new_paragraph('**IMPORTANT:** The images of the pipeline are for reference only. The actual pipeline may differ from the images. Please refer to the number of L and T joints and the length of pipe required for the actual pipeline. \
                                 The number of standard lengths of pipe required is also provided if the standard length of pipe is set. If the standard length of pipe is not set, the length of pipe to purchase is provided instead. \
                Assumptions made in the calculation of the number of L and T joints and the length of pipe required are as follows:')
            mdfile.new_paragraph()
            mdfile.new_list(['The input and output points are the endpoints of the pipeline.', \
                             'The input and output points are L joints.', 'There are no obstacles in the pipeline.'])
            mdfile.new_paragraph()
            mdfile.new_header(level=1, title='Results')
            mdfile.new_paragraph(f'The input coordinates are *{inp_loc[0]}*, *{inp_loc[1]}*, *{inp_loc[2]}*.')
            mdfile.new_paragraph(f'Number of output coordinates: *{len(out_loc)}*')
            for i in range(len(out_loc)):
                mdfile.new_paragraph(f'Output coordinates {i+1}: *{out_loc[i][0]}*, *{out_loc[i][1]}*, *{out_loc[i][2]}*.')
            mdfile.new_paragraph()
            mdfile.new_paragraph('The following are the results of the shortest path between the input and output points.')
            mdfile.new_paragraph(f'**Number of L joints:** *{mydict["L Joints"]}*')
            mdfile.new_paragraph(f'**Number of T joints:** *{mydict["T Joints"]}*')
            mdfile.new_paragraph(f'**Number of Pipe Segments:** *{mydict["Pipe Segments"]}*')
            mdfile.new_paragraph(f'**Length of Pipe Required:** *{mydict["Pipe Length"]:.2f} mm*')
            try:
                if sl is not None:
                    mdfile.new_paragraph(f'**Standard Length:** *{sl:.2f} mm*')
                    mdfile.new_paragraph(f'**Number of Standard Lengths:** *{math.ceil(mydict["Pipe Length"]/sl):.0f}*')
            except NameError:
                mdfile.new_paragraph('**Standard length not set.**')
                mdfile.new_paragraph(f'**Length of Pipe to Purchase:** *{math.ceil(mydict["Pipe Length"]/10)*10:.2f} mm*')
            mdfile.new_paragraph()
            mdfile.new_header(level=1, title='Bill of Materials')
            mdfile.new_paragraph('The following is the bill of materials for the pipeline.')
            mdfile.new_paragraph()
            pricing = [['Piping (per mm)', 0.0099],['L Joint', 2.75], ['T Joint', 1.43]]
            mat_list = []
            mat_list.extend(['Item', 'Quantity (units)', 'Unit Price (AUD)', 'Total Price (AUD)'])
            try:
                if sl is not None:
                    mat_list.extend([f'Standard Pipe Segments ({sl})', f'{math.ceil(mydict["Pipe Length"]/sl):.0f}', f'{0.0099*sl}', f'{(math.ceil(mydict["Pipe Length"]/sl))*0.0099:.2f}'])
            except NameError:
                mat_list.extend(['Pipe', f'{mydict["Pipe Segments"]}', 0.0099, f'{0.0099*mydict["Pipe Segments"]:.2f}'])
            mat_list.extend(['L Joint', f'{mydict["L Joints"]}', 2.75, 2.75*mydict["L Joints"]])
            mat_list.extend(['T Joint', f'{mydict["T Joints"]}', 1.43, 1.43*mydict["T Joints"]])
            mat_list.extend(['Total', '', '', f'${(0.0099*mydict["Pipe Segments"] + 2.75*mydict["L Joints"] + 1.43*mydict["T Joints"]):.2f}'])
            mdfile.new_table(columns=4, rows=5, text=mat_list, text_align='center')
            mdfile.new_paragraph()
            mdfile.new_header(level=1, title='Pipleline Drawings')
            mdfile.new_paragraph('The following pages contain images of the suggested pipeline from different angles.')
            l_images = []
            for i in range(len(cpos)):
                l_images.append(f'{folder}/temp/{cpos[i]}.png')
            mdfile.new_paragraph()
            mdfile.new_line(mdfile.new_inline_image(text='Top View', path=l_images[0]))
            mdfile.new_paragraph()
            mdfile.new_line(mdfile.new_inline_image(text='Top Right Isometric View', path=l_images[1]))
            mdfile.new_paragraph()
            mdfile.new_line(mdfile.new_inline_image(text='Front View', path=l_images[2]))
            mdfile.new_paragraph()
            mdfile.new_line(mdfile.new_inline_image(text='Right View', path=l_images[3]))
            mdfile.new_paragraph()
            mdfile.new_line(mdfile.new_inline_image(text='Bottom View', path=l_images[4]))
            mdfile.new_paragraph()
            mdfile.new_line(mdfile.new_inline_image(text='Bottom Right Isometric View', path=l_images[5]))
            mdfile.new_paragraph()
            mdfile.create_md_file()
            if not os.path.exists(f'{folder}/reports'):
                os.makedirs(f'{folder}/reports')
            try:
                doc = pypandoc.convert_file('report.md', 'pdf', outputfile=f'{folder}/reports/report.pdf', extra_args=['-V', 'geometry:margin=1in'])
            except RuntimeError as e:
                print(e)
                print("Error converting to pdf. Install MikTeX for direct PDF conversion. Word file generated instead.")
                doc = pypandoc.convert_file('report.md', 'docx', outputfile=f'{folder}/reports/report.docx')
            os.remove('report.md')
            print("Report generated")
        elif command == "help":
            # Command to display available commands and their usage.
            print("setres - set resolution for voxelization.\nLeave empty to use default value (0.05).\nRecommended resolution is 0.05 and must be between 0 and 1.\nMust be set before loading a model. If set after loading a model, the model must be reloaded.\n")
            print("loadmodel - load a model.\nCurrently, only STL files are supported.\nMust be loaded before picking input and output coordinates.\n")
            print("pickio - pick input and output coordinates. Must be done after loading a model.\nClick on a face to select it\nPress the relevant checkbox to ensure correct coordinates are selected.\nThe arrow MUST be visible and facing away from the selected face.\nPress 'i' to select input coordinates.\nPress 'o' to select output coordinates.\nPress 'c' to clear selection.\nPress 'q' to exit selection mode.\n")
            print("setinput - set input coordinates (not recommended))\n")
            print("setoutput - set output coordinates (not recommended))\n")
            print("standardlength - set standard length of pipe.\nMust be set before running algorithm. \nIf not set, the total length of pipe to purchase will be provided instead.\nIf set, the number of standard lengths of pipe required will be provided instead.\nIf set, the standard length of pipe must be greater than 0 and in mm.\n")
            print("run - run algorithm.\nMust be run after setting input and output coordinates.\nMust be run after setting standard length of pipe (optional).\n")
            print("generatereport - generate report.\nMust be run after running algorithm.\nReport will be generated in the same directory as the program.\nReport will contain results and images of the pipeline.\nReport will be generated in PDF format if MikTeX is installed. Otherwise, it will be generated in Word format.\n")
            print("exit - exit program")

        elif command == "exit":
            # Command to exit the program.
            sys.exit()
        else:
            # Handle invalid commands.
            print("Invalid command")
