# Dijkstra algorithm in 3D
# Implemented from https://lunalux.io/dijkstras-algorithm-for-grids-in-python/
# Author: Rushabh Patel
# Date: 2023-07-22
# Version: 1.0

import numpy as np
debug = False

def valid_node(node, size_of_grid):
    """
    Checks if the given node is a valid node within the specified grid.

    Parameters:
        node (list): The node coordinates [x, y, z] to check for validity.
        size_of_grid (list): The size of the grid [grid_size_x, grid_size_y, grid_size_z].

    Returns:
        bool: True if the node is valid within the grid, False otherwise.
    """
    if node[0] < 0 or node[0] >= size_of_grid[0]:
        return False
    elif node[1] < 0 or node[1] >= size_of_grid[1]:
        return False
    elif node[2] < 0 or node[2] >= size_of_grid[2]:
        return False
    else:
        return True
    
def x_up(node):
    """
    Returns the node above the given node along the x-axis.

    Parameters:
        node (list): The node coordinates [x, y, z] for which to find the node above.

    Returns:
        list: The coordinates of the node above [x, y, z].
    """
    return [node[0]+1, node[1], node[2]]

def x_down(node):
    """
    Returns the node below the given node along the x-axis.

    Parameters:
        node (list): The node coordinates [x, y, z] for which to find the node below.

    Returns:
        list: The coordinates of the node below [x, y, z].
    """
    return [node[0]-1, node[1], node[2]]

def y_up(node):
    """
    Returns the node right of the given node along the y-axis.

    Parameters:
        node (list): The node coordinates [x, y, z] for which to find the node below.

    Returns:
        list: The coordinates of the node below [x, y, z].
    """
    return [node[0], node[1]+1, node[2]]

def y_down(node):
    """
    Returns the node left of the given node along the y-axis.

    Parameters:
        node (list): The node coordinates [x, y, z] for which to find the node below.

    Returns:
        list: The coordinates of the node below [x, y, z].
    """
    return [node[0], node[1]-1, node[2]]

def z_up(node):
    """
    Returns the node in front of the given node along the z-axis.

    Parameters:
        node (list): The node coordinates [x, y, z] for which to find the node below.

    Returns:
        list: The coordinates of the node below [x, y, z].
    """
    return [node[0], node[1], node[2]+1]

def z_down(node):
    """
    Returns the node behind the given node along the z-axis.

    Parameters:
        node (list): The node coordinates [x, y, z] for which to find the node below.

    Returns:
        list: The coordinates of the node below [x, y, z].
    """
    return [node[0], node[1], node[2]-1]

def backtrack(initial_node, desired_node, distances):
    """
    Backtracks the path from the desired_node to the initial_node based on the calculated distances.

    Parameters:
        initial_node (list): The coordinates [x, y, z] of the initial node in the grid.
        desired_node (list): The coordinates [x, y, z] of the desired node in the grid.
        distances (numpy.ndarray): A 3D numpy array containing the calculated distances.

    Returns:
        list: The list of nodes representing the shortest path from initial_node to desired_node.
    """
    # Note: The function constructs the shortest path in reverse, starting from the desired_node
    # and backtracking through nodes with decreasing distances until reaching the initial_node.
    path = [desired_node]
    size_of_grid = [distances.shape[0], distances.shape[1], distances.shape[2]]
    while True:
        potential_distances = []
        potential_nodes = []
        directions = [x_up, x_down, y_up, y_down, z_up, z_down]
        for direction in directions:
            node = direction(path[-1])
            if valid_node(node, size_of_grid):
                potential_nodes.append(node)
                potential_distances.append(distances[node[0], node[1], node[2]])
        least_distance_index = np.argmin(potential_distances)
        path.append(potential_nodes[least_distance_index])
        if path[-1][0] == initial_node[0] and path[-1][1] == initial_node[1] and path[-1][2] == initial_node[2]:
            break
    return list(reversed(path))

def dijkstra(initial_node, desired_node, obstacles):
    '''
    Dijkstras algorithm for finding the shortest path between two nodes in a 3d grid
    Args:
        initial_node: initial node in the grid
        desired_node: desired node in the grid (coordinates as [x, y, z])
        obstacles: list of obstacles in the grid
    Returns:
        path: list of nodes in the shortest path
    '''
    # Note: To handle obstacles in the grid, we convert obstacles to a large value (1000) and add 1.
    # This ensures that obstacles are avoided while calculating the shortest path.
    # Note: The function uses Dijkstra's algorithm to find the shortest path in a 3D grid.
    # It initializes distances from the initial_node to all other nodes as infinity,
    # then explores adjacent nodes and updates their distances if a shorter path is found.
    # The visited array is used to track visited nodes and avoid revisiting them.
    obstacles = obstacles.copy()
    obstacles *= 1000
    obstacles += np.ones(obstacles.shape, dtype=int)
    if debug:
        print(np.max(obstacles))
    obstacles[initial_node[0], initial_node[1], initial_node[2]] = 0
    obstacles[desired_node[0], desired_node[1], desired_node[2]] = 0
    size_of_map = [obstacles.shape[0], obstacles.shape[1], obstacles.shape[2]]
    visited = np.zeros([size_of_map[0], size_of_map[1], size_of_map[2]], bool)
    distances = np.ones([size_of_map[0], size_of_map[1], size_of_map[2]]) * np.inf
    distances[initial_node[0], initial_node[1], initial_node[2]] = 0
    current_node = [initial_node[0], initial_node[1], initial_node[2]]
    steps = 0
    while True:
        directions = [x_up, x_down, y_up, y_down, z_up, z_down]
        for direction in directions:
            potential_node = direction(current_node)
            if steps == 0 and debug:
                print('potential node = ', potential_node)
            if valid_node(potential_node, size_of_map):#boundary check
                if not visited[potential_node[0], potential_node[1], potential_node[2]]:
                    distance = distances[current_node[0], current_node[1], current_node[2]] + obstacles[potential_node[0], potential_node[1], potential_node[2]]
                    #update distance if it is the shortest discovered
                    if distance < distances[potential_node[0], potential_node[1], potential_node[2]]:
                        distances[potential_node[0], potential_node[1], potential_node[2]] = distance
        visited[current_node[0], current_node[1], current_node[2]] = True
        t = distances.copy()
        t[np.where(visited)] = np.inf
        node_index = np.argmin(t)
        node_x = node_index//(size_of_map[1]*size_of_map[2])
        node_y = (node_index%(size_of_map[1]*size_of_map[2]))//size_of_map[2]
        node_z = node_index%size_of_map[2]
        if steps == 0 and debug:
            print(node_x, node_y, node_z)
        current_node = [node_x, node_y, node_z]
        if steps == 0 and debug:
            print('current step = ', steps)
            print('current node = ', current_node)
        if current_node[0] == desired_node[0] and current_node[1] == desired_node[1] and current_node[2] == desired_node[2]:
            break
        steps += 1
    print('Number of iterations = ', steps)
    return backtrack(initial_node, desired_node, distances)