import maya.OpenMaya as om
import maya.api.OpenMaya as om2
from maya import cmds

import math


def revert_API_matrix_types(om2_mmatrix):
    """
    Revert Maya.api.OpenMaya to maya.OpenMaya MMatrix() object type.
    Args:
        om2_mmatrix(om2.MMatrix()):

    Returns:

    """

    # Create a new MMatrix (old API)
    old_matrix = om.MMatrix()

    # Extract the values from the new MMatrix (maya.api.OpenMaya.MMatrix)
    for i in range(4):
        for j in range(4):
            value = om2_mmatrix[i * 4 + j]
            # Set the value in the corresponding position of the old MMatrix
            om.MScriptUtil.setDoubleArray(old_matrix[i], j, value)

    return old_matrix

def normalise_vector(vector=(0, 0, 0)):
    """
    Normalise our vector.
    Args:
        vector(tuple):

    Returns:

    """

    normal = om.MVector(vector[0], vector[1], vector[2]).normal()
    return (normal.x, normal.y, normal.z)


def cross_product(vec1=(0.0,0.0,0.0),vec2=(0.0,0.0,0.0)):
    """
    Calculate cross product of two vectors
    Args:
        vec1(tuple):
        vec2(tuple):

    Returns:

    """

    vec1 = om.MVector(vec1[0], vec1[1], vec1[2])
    vec2 = om.MVector(vec2[0], vec2[1], vec2[2])

    _cross_product = vec1 ^ vec2

    return (_cross_product.x, _cross_product.y, _cross_product.z)


def offset_vector(point1=(0.0,0.0,0.0),point2=(0.0,0.0,0.0)):
    """
    Calculate our offset vector
    Args:
        point1:
        point2:

    Returns:

    """

    pnt_1 = om.MPoint(point1[0], point1[1], point1[2], 1.0)
    pnt_2 = om.MPoint(point2[0], point2[1], point2[2], 1.0)

    vec = pnt_2 - pnt_1

    return (vec.x, vec.y, vec.z)


def vector_matrix_mult(vector, matrix):
    """
    Multiplies vector by matrix
    Args:
        vector:
        matrix:

    Returns:

    """

    vector = om.MVector(vector[0], vector[1], vector[2])

    if matrix != om.MMatrix.identity:
        vector *= matrix

    return [vector.x, vector.y, vector.z]

def position_dot_product(point1=(0.0,0.0,0.0),point2=(0.0,0.0,0.0)):
    """
    Get a positional difference between two points.
    Args:
        point1(tuple):
        point2(tuple):

    Returns:

    """

    _point_1 = om.MPoint((point1[0], point1[1], point1[2]), 1.0)
    _point_2 = om.MPoint((point2[0], point2[1], point2[2]), 1.0)

    return om.MVector(_point_1 - _point_2).length()


def print_matrix(matrix):
    """
    Print our om2.MMatrix()

    Args:
        matrix(om2.MMatrix()):

    Returns:

    """

    for i in range(4):
        row = []
        for j in range(4):
            row.append(matrix[i*4 + j])
        print(' '.join(['{:.2f}'.format(item) for item in row]))


def setMatrixValues(matrix, row, col, value):
    """
    Set Matrix Values
    Args:
        matrix:
        row:
        col:
        value:

    Returns:

    """

    matrixUtil = om2.MScriptUtil()
    matrixUtil.createFromDouble(value)
    valuePtr = matrixUtil.asDoublePtr()

    om2.MScriptUtil.setDouble4ArrayItem(matrix, row, col, valuePtr)


def get_rotation(matrix, rotation_order="xyz"):
    """
    Get our rotation values from a matrix.
    Args:
        matrix(om.MMatrix()):
        rotation_order(str)/(int):

    Returns:

    """

    radian = 180.0/math.pi

    if type(rotation_order) != str:
        rot_orders = {'xyz':0,'yzx':1,'zxy':2,'xzy':3,'yxz':4,'zyx':5}

        rotation_order = int(rotation_order)

    transformMatrix = om.MTransformationMatrix(matrix)

    euler_rotation = transformMatrix.eulerRotation()

    euler_rotation.reorderIt(rotation_order)

    return (euler_rotation.x*radian, euler_rotation.y*radian, euler_rotation.z*radian)


# TODO: CURRENT ISSUE: we are already worldspace here if we set it, so in our main matrix it will multiply again
# by worldspace. translation isnt separated so it messes it up!.
def get_matrix(transform, ns=None, local=True):
    """
    TODO: Needs optimising.
    Get our matrix.
    Args:
        transform:
        ns:
        local:

    Returns:

    """

    obj_query = transform
    if ns:
        obj_query = f"{ns}:{transform}"

    if not cmds.objExists(obj_query):
        raise Exception('Object "' + transform + '" does not exist!')

    matrix_attr = 'worldMatrix[0]'
    if local:
        matrix_attr = 'matrix'

    # Get time
    _matrix = om2.MMatrix()

    _matrix = cmds.getAttr(transform + "." + matrix_attr)

    rot_mat = [ _matrix[0], _matrix[1], _matrix[2],
                0, _matrix[4], _matrix[5], _matrix[6],
                0, _matrix[8], _matrix[9], _matrix[10],
                0, 0, 0, 0, 1]

    rotation_matrix = om2.MMatrix(rot_mat)

    transform_matrix = om2.MTransformationMatrix(rotation_matrix)

    euler_rotation = transform_matrix.rotation(asQuaternion=False)

    orient_x = om2.MAngle(euler_rotation.x, om2.MAngle.kRadians).asDegrees()
    orient_y = om2.MAngle(euler_rotation.y, om2.MAngle.kRadians).asDegrees()
    orient_z = om2.MAngle(euler_rotation.z, om2.MAngle.kRadians).asDegrees()

    matrix = buildMatrix(
        translate=(
            _matrix[12], _matrix[13], _matrix[14]
        ),
        orient=(
            orient_x,
            orient_y,
            orient_z
        ), ws=False,
        transform=transform # mess sort out
    )

    return matrix


# TODO: be careful with this as we are only getting joint orientation, it's not WS at all.
def buildMatrix(translate=(0,0,0), orient=(0,0,0), scale=(1,1,1), ws=False, transform=None):
    """
    Build our matrix from our cache!
    Args:
        translate:
        orient:
        scale:
        ws:
        transform:

    Returns:

    """

    # WS flag is ONLY used NOT with getMatrix()
    rotX = math.radians(orient[0])
    rotY = math.radians(orient[1])
    rotZ = math.radians(orient[2])

    rot_matrix = om2.MEulerRotation(rotX, rotY, rotZ).asMatrix()

    scale_matrix = om2.MMatrix()
    scale_matrix[0] = scale[0]
    scale_matrix[5] = scale[1]
    scale_matrix[10] = scale[2]

    combined_matrix = scale_matrix * rot_matrix

    # set our translation.
    combined_matrix[12] = translate[0]
    combined_matrix[13] = translate[1]
    combined_matrix[14] = translate[2]

    if ws and transform:  # only use when we also have an already instanced object.
        world_matrix = cmds.xform(transform, q=True, matrix=True, ws=True)
        new_matrix = om2.MMatrix(world_matrix)
        combined_matrix = new_matrix * combined_matrix

    return combined_matrix


def build_matrix_from_vectors(translate=(0,0,0),xAxis=(1,0,0),yAxis=(0,1,0),zAxis=(0,0,1)):
    """
    Create a matrix from vectors
    Args:
        translate:
        xAxis:
        yAxis:
        zAxis:

    Returns:

    """

    # Create transformation matrix from input vectors
    matrix = om.MMatrix()
    om.MScriptUtil.setDoubleArray(matrix[0], 0, xAxis[0])
    om.MScriptUtil.setDoubleArray(matrix[0], 1, xAxis[1])
    om.MScriptUtil.setDoubleArray(matrix[0], 2, xAxis[2])
    om.MScriptUtil.setDoubleArray(matrix[1], 0, yAxis[0])
    om.MScriptUtil.setDoubleArray(matrix[1], 1, yAxis[1])
    om.MScriptUtil.setDoubleArray(matrix[1], 2, yAxis[2])
    om.MScriptUtil.setDoubleArray(matrix[2], 0, zAxis[0])
    om.MScriptUtil.setDoubleArray(matrix[2], 1, zAxis[1])
    om.MScriptUtil.setDoubleArray(matrix[2], 2, zAxis[2])
    om.MScriptUtil.setDoubleArray(matrix[3], 0, translate[0])
    om.MScriptUtil.setDoubleArray(matrix[3], 1, translate[1])
    om.MScriptUtil.setDoubleArray(matrix[3], 2, translate[2])

    return matrix


def buildRotation(aim_vector, up_vector=(0, 1, 0), aim_axis='x', up_axis='y'):
    """
    # modified function from Grant Laker's repository under MIT License.
    Args:
        aim_vector:
        up_vector:
        aim_axis:
        up_axis:

    Returns:

    """

    # Check negative axis
    negate_aim_axis = False
    negate_up_vector = False
    if aim_axis[0] == '-':
        aim_axis = aim_axis[1]
        negate_aim_axis = True
    if up_axis[0] == '-':
        up_axis = up_axis[1]
        negate_up_vector = True

    # Check valid axis
    axis_list = ['x', 'y', 'z']

    if not axis_list.count(aim_axis):
        raise Exception('invalid aim axis')
    if not axis_list.count(up_axis):
        raise Exception('invalid up axis')
    if aim_axis == up_axis:
        raise Exception('aim and up axis are not unique.')

    # calculate cross axis
    axis_list.remove(aim_axis)
    axis_list.remove(up_axis)
    cross_axis = axis_list[0]

    aim_vector = normalise_vector(aim_vector)
    if negate_aim_axis:
        aim_vector = (-aim_vector[0], -aim_vector[1], -aim_vector[2])

    up_vector = normalise_vector(up_vector)
    if negate_up_vector:
        up_vector = (-up_vector[0], -up_vector[1], -up_vector[2])

    # Get cross product vector
    cross_vector = (0, 0, 0)

    if (aim_axis == 'x' and up_axis == 'z') or (aim_axis == 'z' and up_axis == 'y'):
        cross_vector = cross_product(up_vector, aim_vector)
    else:
        cross_vector = cross_product(aim_vector, up_vector)
    # Recalculate upVector (orthogonalize)
    if (aim_axis == 'x' and up_axis == 'z') or (aim_axis == 'z' and up_axis == 'y'):
        up_vector = cross_product(aim_vector, cross_vector)
    else:
        up_vector = cross_product(cross_vector, aim_vector)

    # Build axis dictionary
    axis_dict = {aim_axis: aim_vector, up_axis: up_vector, cross_axis: cross_vector}
    # Build rotation matrix
    mat = build_matrix_from_vectors(xAxis=axis_dict['x'], yAxis=axis_dict['y'], zAxis=axis_dict['z'])

    # Return rotation matrix
    return mat