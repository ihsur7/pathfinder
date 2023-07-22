# Plotter class for interactive visualization of voxel models
# Author: Rushabh Patel
# Date: 2023-07-22
# Version: 1.0

import warnings
import numpy as np

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import pyvista as pv

class Plotter():    
    """
    Plotter class for interactive visualization of voxel models.

    This class provides an interactive visualization environment using the pyvista library to display voxel models.
    Users can interactively select input and output points, toggle grid lines, and view the 3D axes.
    
    Attributes:
        vx (pyvista.UniformGrid): Voxel model represented as a pyvista UniformGrid.
        pts (numpy.ndarray): Array containing the points of interest in the voxel model.
        flat (numpy.ndarray or None): Array representing scalar values for coloring the voxels (optional).
        picker (bool): If True, enable interactive element picking for the plot.
        grid (bool): If True, display grid lines on the plot.
        axes (bool): If True, display axes on the plot.
    """
    def __init__(self, vx, pts, flat = None, picker = True, grid = True, axes = True, **kwargs):
        """
        Initialize the Plotter object.

        Parameters:
            vx (pyvista.UniformGrid): Voxel model represented as a pyvista UniformGrid.
            pts (numpy.ndarray): Array containing the points of interest in the voxel model.
            flat (numpy.ndarray or None): Array representing scalar values for coloring the voxels (optional).
            picker (bool): If True, enable interactive element picking for the plot.
            grid (bool): If True, display grid lines on the plot.
            axes (bool): If True, display axes on the plot.
            **kwargs: Additional keyword arguments to pass to the Plotter.
        """
        self.inp = None
        self.out = None
        self.vx = vx.copy(deep=True)
        self.flat = flat
        self.pts = pts
        self.negx = False
        self.negy = False
        self.negz = False
        self.x_pos = None
        self.y_pos = None
        self.z_pos = None
        self.p = pv.Plotter(window_size=[1300, 1300])
        self.p.add_mesh(self.vx, color=True, show_edges=True, scalars = self.flat, cmap=['red', 'gray'], opacity=1)
        if grid:
            self.p.show_grid()
        # if kwargs.get('axes') == True:
        if axes:
            self.p.show_axes_all()
        self.min_x = self.vx.bounds[0]
        self.max_x = self.vx.bounds[1]
        self.min_y = self.vx.bounds[2]
        self.max_y = self.vx.bounds[3]
        self.min_z = self.vx.bounds[4]
        self.max_z = self.vx.bounds[5]
        if picker:
            self.p.enable_element_picking(callback = self.callback, mode='face', left_clicking = True, pickable_window=True, picker='cell', show_message=False)
            self.p.add_text('-x', position=(800, 80), font_size=20, color='red')
            self.p.add_text('-y', position=(1000, 80), font_size=20, color='green')
            self.p.add_text('-z', position=(1200, 80), font_size=20, color='blue')
            self.p.add_checkbox_button_widget(callback = self.callback_negx, value = False, position = (800, 20), color_on = 'red')
            self.p.add_checkbox_button_widget(callback = self.callback_negy, value = False, position = (1000, 20), color_on = 'green')
            self.p.add_checkbox_button_widget(callback = self.callback_negz, value = False, position = (1200, 20), color_on = 'blue')
            self.p.add_key_event('i', self.callback_i)
            self.p.add_key_event('o', self.callback_o)
            self.p.add_text('Click on a face to select it', position='upper_left', name='instruction')
            self.p.add_key_event('c', self.clear_sel)
        if flat is not None:
            self.p.remove_scalar_bar()

    def clear_sel(self):
        """
        Clear the selected input and output points from the plot.
        """
        self.p.remove_actor('io')
        self.inp = None
        self.out = None

    def callback_i(self):
        """
        Callback function for the 'i' key press event. Sets the selected point as the input point.
        """
        self.p.remove_actor('io')
        try:
            assert self.x_pos is not None and self.y_pos is not None and self.z_pos is not None, 'Please select a point'
            assert self.out != [self.x_pos, self.y_pos, self.z_pos], 'Input cannot be the same as output'
            self.inp = [self.x_pos, self.y_pos, self.z_pos]
            self.p.add_text(f'Input: {self.inp}\nOutput: {self.out}', position=('upper_right'), name='io')
        except AssertionError as e:
            self.p.add_text(f'Input: {self.inp}\nOutput: {self.out}', position=('upper_right'), name='io')
            print(e)

    def callback_o(self):
        """
        Callback function for the 'o' key press event. Sets the selected point as the output point.
        """
        self.p.remove_actor('io')
        try:
            assert self.x_pos is not None and self.y_pos is not None and self.z_pos is not None, 'Please select a point'
            assert self.inp != [self.x_pos, self.y_pos, self.z_pos], 'Output cannot be the same as input'
            out_pos = [self.x_pos, self.y_pos, self.z_pos]
            if self.out is None:
                self.out = [out_pos]
            elif self.out is not None:
                if len(self.out) == 2:
                    self.out.pop(0)
                if out_pos not in self.out:
                    self.out.append(out_pos)
            self.p.add_text(f'Input: {self.inp}\nOutput: {self.out}', position=('upper_right'), name='io')
        except AssertionError as e:
            self.p.add_text(f'Input: {self.inp}\nOutput: {self.out}', position=('upper_right'), name='io')
            print(e)

    def get_i(self):
        """
        Get the currently selected input point.

        Returns:
            list or None: The (x, y, z) coordinates of the selected input point, or None if not selected.
        """
        return self.inp
    
    def get_o(self):
        """
        Get the currently selected output points as a flattened list.

        Returns:
            list: A flattened list of (x, y, z) coordinates of the selected output points.
        """
        flat_out = [item for sublist in self.out for item in sublist]
        return flat_out

    def callback_negx(self, value):
        """
        Callback function for the negative x-axis checkbox widget.

        Parameters:
            value (bool): The value of the checkbox (True if checked, False otherwise).
        """
        self.negx = value
    
    def callback_negy(self, value):
        """
        Callback function for the negative y-axis checkbox widget.

        Parameters:
            value (bool): The value of the checkbox (True if checked, False otherwise).
        """
        self.negy = value

    def callback_negz(self, value):
        """
        Callback function for the negative z-axis checkbox widget.

        Parameters:
            value (bool): The value of the checkbox (True if checked, False otherwise).
        """
        self.negz = value
    
    def callback(self, pos):
        """
        Callback function for interactive element picking.

        Parameters:
            pos (pyvista.PickInfo): Information about the picked element.
        """
        self.p.remove_actor('instruction')
        self.p.remove_actor('coords')
        self.p.remove_actor('arrow')
        pos_arr = np.array([[pos.bounds[0], pos.bounds[1]], [pos.bounds[2], pos.bounds[3]], [pos.bounds[4], pos.bounds[5]]], dtype=np.float32)
        for i in range(3):
            if pos_arr[i][0] == pos_arr[i][1]:
                if i == 0:
                    if self.negx:
                        self.x_pos = pos_arr[i][0]-0.5
                        adir = np.array([-1, 0, 0])
                    else:
                        self.x_pos = pos_arr[i][0]+0.5
                        adir = np.array([1, 0, 0])
                    self.y_pos = pos_arr[i+1][0] + (pos_arr[i+1][1] - pos_arr[i+1][0])/2
                    self.z_pos = pos_arr[i+2][0] + (pos_arr[i+2][1] - pos_arr[i+2][0])/2
                elif i == 1:
                    self.x_pos = pos_arr[i-1][0] + (pos_arr[i-1][1] - pos_arr[i-1][0])/2
                    if self.negy:
                        self.y_pos = pos_arr[i][0]-0.5
                        self.adir = np.array([0, -1, 0])
                    else:
                        self.y_pos = pos_arr[i][0]+0.5
                        adir = np.array([0, 1, 0])
                    self.z_pos = pos_arr[i+1][0] + (pos_arr[i+1][1] - pos_arr[i+1][0])/2
                elif i == 2:
                    self.x_pos = pos_arr[i-2][0] + (pos_arr[i-2][1] - pos_arr[i-2][0])/2
                    self.y_pos = pos_arr[i-1][0] + (pos_arr[i-1][1] - pos_arr[i-1][0])/2
                    if self.negz:
                        self.z_pos = pos_arr[i][0]-0.5
                        adir = np.array([0, 0, -1])
                    else:
                        self.z_pos = pos_arr[i][0]+0.5
                        adir = np.array([0, 0, 1])
        self.p.add_text(f'Coodinates: {(self.x_pos, self.y_pos, self.z_pos)}', shadow=True, color='black', position='lower_left', viewport=True, name='coords')
        self.p.add_arrows(cent = np.array([self.x_pos, self.y_pos, self.z_pos]), direction = adir, color='red', name='arrow', mag=1, pickable=False)
        self.p.add_text(f'Input: {self.inp}\nOutput: {self.out}', position=('upper_right'), name='io')


    def _update(self):
        self.output.overwrite(self.point)

    def update_x(self, value):
        """
        Update the x-coordinate of a selected point (internal use).

        Parameters:
            value (int): The new x-coordinate value.
        """
        self.point.points[0][0] = int(value)
        self._update()

    def update_y(self, value):
        """
        Update the y-coordinate of a selected point (internal use).

        Parameters:
            value (int): The new y-coordinate value.
        """
        self.point.points[0][1] = int(value)
        self._update()

    def update_z(self, value):
        """
        Update the z-coordinate of a selected point (internal use).

        Parameters:
            value (int): The new z-coordinate value.
        """
        self.point.points[0][2] = int(value)
        self._update()

    def add_part(self, part):
        """
        Add a part to the plot.

        Parameters:
            part (pyvista.UnstructuredGrid): Part to add to the plot as a pyvista UnstructuredGrid.
        """
        self.p.add_mesh(part, color='red', show_edges=True, opacity=1)

    def plot(self):
        """
        Display the plot.
        """
        self.p.show()