from maya import cmds
import maya.OpenMaya as om
import maya.utils

from . import utils
from . import ops


def duplicate_joint(joint, name=None):
    """
    duplicate our joint object(s)
    :param joint: our joint to duplicate
    :param name: rename the joint
    :return:
    """

    if not cmds.objExists(joint):
        raise Exception(f"{joint} does not exist.")
    if not name:
        name = joint+"_duplicate"
    if cmds.objExists(str(name)):
        raise Exception(f"{name} already exists.")


    duplicated_joint = cmds.duplicate(joint)[0]
    if name:
        duplicated_joint = cmds.rename(duplicated_joint, name+joint)

    attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v', 'radius']
    for attr in attributes:
        cmds.setAttr(duplicated_joint+"."+attr, l=False, cb=True)

    return duplicated_joint


def reorder_joints(joint_list):
    """
    This function would rarely be used, however, re-orders where a list might have ordered joints wrong.
    :param joint_list: list of joints.
    :return: list of ordered joints.
    """

    joint_hiearchy = {}

    for joint in joint_list:
        parent = cmds.listRelatives(joint, parent=True)
        joint_hiearchy[joint] = parent[0] if parent else None

    root_joint = None
    for joint in joint_list:
        if joint_hiearchy[joint] is None:
            root_joint = joint
            break

    ordered_joints = [root_joint]
    current_joint = root_joint

    while True:
        children = [joint for joint, parent in joint_hiearchy.items() if parent == current_joint]
        if not children:
            break
        next_joint = children[0]
        ordered_joints.append(next_joint)
        current_joint = next_joint

    return ordered_joints

def getMObject(object):
    """
    Return an MObject data type of our object
    :param object: Object pointer
    :return: MObject
    """

    # Check input object
    if not cmds.objExists(object):
        raise Exception(f"{object}' does not exist.")

    selectionList = om.MSelectionList()
    om.MGlobal.getSelectionListByName(object,selectionList)
    mObject = om.MObject()
    selectionList.getDependNode(0,mObject)

    return mObject

def get_position(point):
    """
    With wildcard position data representing a transform, check typing and return.
    :param point: Wildcard position data.
    :return:
    """
    # Initialize point value
    pos = []

    # Determine point type
    if (type(point) == list) or (type(point) == tuple):
        pos = point[0:3]

    elif type(point) == str:

        # Check Transform
        mObject = getMObject(point)
        if mObject.hasFn(om.MFn.kTransform):
            try:
                pos = cmds.xform(point, q=True, ws=True, rp=True)
            except:
                pass

        if not pos:
            try:
                pos = cmds.pointPosition(point)
            except:
                pass

        if not pos:
            try:
                pos = cmds.xform(point, q=True, ws=True, rp=True)
            except:
                pass

    return pos


def fix_joint_orientations(joint, aim_axis="x", up_axis="y", up_vector=(0, 1, 0)):
    """
    Called after every skeleton generation event.
    Using bungnoid's aiming functions in the gllibary, fix our joint's orientations (similar to aim constraint).
    :param joint: joint object
    :param aim_axis: string representing axis that aims to child.
    :param up_axis: string representing up-axis (secondary)
    :param up_vector: string representing up vector for calculation.
    :return:
    """
    child_list = cmds.listRelatives(joint, c=1)
    child_jnt_list = cmds.listRelatives(joint, c=1, type="joint", pa=True)

    if child_list:
        child_list = cmds.parent(child_list, w=True)  # unparent joint children.

    if not child_jnt_list:
        cmds.setAttr(joint + ".jo", 0, 0, 0)

    else:
        parent_jnt_mat = om.MMatrix()
        parent_jnt = cmds.listRelatives(joint, p=True, pa=True)

        if parent_jnt:
            parent_jnt_mat = ops.get_matrix(parent_jnt[0])
            parent_jnt_mat = ops.revert_API_matrix_types(parent_jnt_mat)


        # calculate aim vector

        pos_1 = get_position(joint)
        pos_2 = get_position(child_jnt_list[0])
        aim_vector = ops.offset_vector(pos_1, pos_2)

        # main target mat
        target_mat = ops.buildRotation(aim_vector, upVector=up_vector,
                                       aimAxis=aim_axis, upAxis=up_axis)


        ori_mat = target_mat * parent_jnt_mat.inverse()


        # why is this 0?
        rotation_order = cmds.getAttr(joint+".ro")
        ori_rotation = ops.get_rotation(ori_mat, rotation_order)

        cmds.setAttr(joint + '.r', 0, 0, 0)
        cmds.setAttr(joint + '.jo', ori_rotation[0], ori_rotation[1], ori_rotation[2])

    if child_list:
        cmds.parent(child_list, joint)


def write_and_construct_matrix(translation, orientation, scale, ws=None):
    """
    [DEFUNCT] but still integrated. Need to remove.
    :param translation: translation data to set to matrix.
    :param orientation: orientation data to set to matrix.
    :param scale: scale data to set to matrix.
    :param ws: whether pass to ops.buildMatrix() using WS argument.
    :return: om2.MMatrix()
    """

    space = False
    transform = None
    if ws:
        space = True
        transform = ws

    matrix = ops.buildMatrix(translate=translation,
                             orient=orientation,
                             scale=scale,
                             ws=space,
                             transform=transform)

    return matrix


def search_ns_items(ns, match=None):
    """
    Search the DAG for items contained within the provided namespace.
    Additionally, match further.
    :param ns: namespace to search within.
    :param match: match string for further match.
    :return: dictionary of {path: object} pairs.
    """

    found_objects = {}
    dag_iter = om.MItDag(om.MItDag.kDepthFirst, om.MFn.kInvalid)

    while not dag_iter.isDone():
        current_obj = dag_iter.currentItem()
        current_path = dag_iter.fullPathName()  # still unique

        if not current_obj.hasFn(om.MFn.kTransform) or current_obj.hasFn(om.MFn.kInvalid):
            dag_iter.next()
            continue

        if ns in dag_iter.partialPathName():
            current_node = dag_iter.partialPathName()
            if ":" in current_node:
                if match:
                    if match in dag_iter.partialPathName():
                        found_objects[current_path] = current_obj
                else:
                    found_objects[current_path] = current_obj
        dag_iter.next()

    return found_objects


def search_items(match):
    """
    Regular search for match pattern in DAG.
    :param match: string to match.
    :return: dictionary of {path: object} pairs.
    """

    found_objects = {}
    dag_iter = om.MItDag(om.MItDag.kDepthFirst, om.MFn.kInvalid)

    while not dag_iter.isDone():
        current_obj = dag_iter.currentItem()
        current_path = dag_iter.partialPathName()

        if not current_obj.hasFn(om.MFn.kTransform) or current_obj.hasFn(om.MFn.kInvalid):
            dag_iter.next()

        fn_dag_node = om.MFnDagNode(current_obj)
        name = fn_dag_node.name()
        if match in name:

            found_objects[current_path] = current_obj

        dag_iter.next()

    return found_objects


def set_and_add_ns(set_ns, add_ns, reset_current=False):
    """
    Set and add an NS to the currently set active namespace.
    :param set_ns: ns to set to current.
    :param add_ns: ns to add to current.
    :param reset_current: set back to root.
    :return: None
    """

    cmds.namespace(set=set_ns)
    cmds.namespace(add=add_ns)

    if reset_current:
        cmds.namespace(set=":")


def filter_for_transforms(objects):

    return [obj for obj in objects if cmds.nodeType(obj) == "transform"]


def relocate_ns(src_ns, parent=None, find_all=True, merge=True, force=True):
    """
    If parent specified, relocate src_ns contents under parent. Otherwise, relocate under root.
    Note: parent should normally be the root.
    :param src_ns: our namespace we're querying.
    :param parent: if parent specified, query with parent.
    :param find_all: find within root namespace.
    :param merge: merge current namespace objects with target namespace.
    :param force: if force, delete the target namespace object.
    :return: None
    """

    cmds.namespace(set=":")

    if find_all:
        ns_list = cmds.namespaceInfo(cmds.namespaceInfo(cur=True), lon=True, r=True)

    if not parent:
        if not cmds.namespace(ex=f"{cmds.namespaceInfo(cur=True)}:{src_ns}"):
            for ns in ns_list:
                if ns.endswith(src_ns):
                    set_and_add_ns(":", src_ns)
                    dst_ns = cmds.namespaceInfo(src_ns, fn=True)
                    cmds.namespace(mv=(ns, dst_ns), f=True)
                    cmds.namespace(rm=ns)
        else:
            maya.utils.executeDeferred('print("namespace: ({}) already exists at target location. ")'.format(src_ns))
    else:
        dst_ns = [path for path in ns_list if path.endswith(parent)]
        if not cmds.namespace(ex=f"{dst_ns[0]}:{src_ns}"):
            for ns in ns_list:
                if ns.endswith(src_ns):  # get our src_ns e.g. "arm"
                    set_and_add_ns(dst_ns[0], src_ns)
                    cmds.namespace(set=":")

                    dst_ns = cmds.namespaceInfo(f"{dst_ns[0]}:{src_ns}", fn=True)  # prevent error

                    cmds.namespace(mv=(ns, dst_ns), f=True)
                    cmds.namespace(rm=ns)
        else:
            maya.utils.executeDeferred('print("namespace: ({}) already exists at target location. ")'.format(src_ns))
            if merge:
                filter_existing = []
                for ns in ns_list:
                    if ns.endswith(src_ns):  # we know our src_ns exists
                        if cmds.namespaceInfo(ns, p=True, bn=True) == parent:
                            existing_list = cmds.namespaceInfo(ns, ls=True)
                            if not existing_list:
                                existing_list = []
                            filter_existing = filter_for_transforms(existing_list)
                            continue

                        src_objects = cmds.namespaceInfo(ns, lod=True)
                        if src_objects:
                            filter_transforms = filter_for_transforms(src_objects)
                            for object in filter_transforms:
                                simple_name = object.split(":")[-1]

                                if f"{dst_ns[0]}:{src_ns}:{simple_name}" in filter_existing:
                                    if force:
                                        cmds.delete(object)
                                    continue
                                cmds.rename(object, f"{dst_ns[0]}:{src_ns}:{simple_name}")

                        cmds.namespace(rm=ns)
            if cmds.namespace(ex=src_ns):
                cmds.namespace(rm=src_ns)


def create_ns(ns, full_parent_path):
    """
    A lighter function that just creates the required namespace from the provided namespace map.
    :param ns: namespace to create
    :param full_parent_path: full parent path to namespace position.
    :return: None
    """
    cmds.namespace(set=":")
    if cmds.namespace(ex=full_parent_path):
        if not cmds.namespace(ex=f"{full_parent_path}:{ns}"):
            set_and_add_ns(full_parent_path, ns, reset_current=True)


def setup_ns_environment(ns="rigdef_1", root="Guides", new_rigdef=False):
    """
    Sets up our namespace environment. If new_rigdef is set to true, then we check for the latest rig_def version
    and increment '+1' to create the latest rig_def version.
    :param ns: rigdef namespace.
    :param root: our root namespace.
    :param new_rigdef: if false, do not create and iterate a new rig_def.
    :return: returns the current namespace.
    """
    cmds.namespace(set=":")
    current_ns = ns

    if not cmds.namespace(ex=root):
        cmds.namespace(add=root)

    cmds.namespace(set=root)

    if not cmds.namespace(ex=ns):
        cmds.namespace(set=":")
        set_and_add_ns(root, ns, reset_current=False)

    else:
        if new_rigdef:
            cmds.namespace(set=":")
            rigdefs = cmds.namespaceInfo(root, ls=True, bn=True)
            latest_rigdef = utils.latest_version(rigdefs)
            current_ns = cmds.namespaceInfo(f"{root}:{latest_rigdef}", bn=True)
            iterated_name = utils.increment_string(current_ns)
            set_and_add_ns(root, iterated_name)

            current_ns = iterated_name

    cmds.namespace(set=":")

    return current_ns

def get_ik_joints(ik):
    """
    Gets the joints affected by the IK system. Normally our IK Joint Chain.
    :param ik: IKHandle object.
    :return: list of affected IK joints.
    """
    if not cmds.objExists(ik):
        raise Exception(f"Object: '{ik}' does not exist.")

    if cmds.objectType(ik) != 'ikHandle':
        raise Exception(f"Object: '{ik}' is nota valid ikHandle.")

    root_joint = cmds.listConnections(ik+'.startJoint',s=True,d=False)[0]
    ik_effector = cmds.listConnections(ik+'.endEffector',s=True,d=False)[0]
    end_joint = cmds.listConnections(ik_effector+'.translateX',s=True,d=False)[0]

    ik_joints = [end_joint]

    while ik_joints[-1] != root_joint:
        ik_joints.append(cmds.listRelatives(ik_joints[-1],p=True)[0])

    ik_joints.reverse()

    return ik_joints

# TODO: Call after IK is built.
def position_pole_vector(ik, f=True, distance=1.0):
    """
    With an IK setup already, position our pole vector.
    :param ik: IKHandle object
    :param f: Whether pole vector object is free to move.
    :param distance: distance set to pole vector.
    :return: pole vector position.
    """

    if cmds.objectType(ik) != "ikHandle":
        raise Exception(f"Object: '{ik}' is not of type IKHandle.")

    if cmds.listConnections(ik+'.ikSolver',s=True,d=False)[0] != 'ikRPsolver':
        raise Exception(f"Object: '{ik}' is not of type ikRPsolver.")

    # get our affected ik joints.
    ik_joints = get_ik_joints(ik)

    pole_vector = cmds.getAttr(ik+".poleVector")[0]
    pole_vector = ops.normalise_vector(pole_vector)

    ik_parent = cmds.listRelatives(ik, p=True)

    if ik_parent:
        ik_matrix = ops.get_matrix(transform=ik_parent[0])
        ik_matrix = ops.revert_API_matrix_types(ik_matrix)
        pole_vector = ops.vector_matrix_mult(pole_vector, ik_matrix)

    root_position = cmds.xform(ik_joints[0], q=True,ws=True,rp=True)
    end_position =  cmds.xform(ik_joints[-1], q=True,ws=True,rp=True)

    if f:
        pole_vector_distance = ops.position_dot_product(root_position, end_position) * distance
        pv_transform = None
        if len(ik_joints) == 3:
            pv_transform = cmds.xform(ik_joints[1],q=True,ws=True,rp=True)

        pole_vector_position = (pv_transform[0]+(pole_vector[0]* pole_vector_distance),pv_transform[1]+
                                (pole_vector[1]* pole_vector_distance),pv_transform[2]+(pole_vector[2]*
                                                                                        pole_vector_distance))
    else:
        pv_transform = cmds.xform(ik_joints[1], q=True, ws=True, rp=True)
        pole_vector_distance = ops.position_dot_product(root_position, pv_transform) * distance
        pole_vector_position = (root_position[0]+(pole_vector[0]*pole_vector_distance),root_position[1]+
                                (pole_vector[1]*pole_vector_distance),root_position[2]+(pole_vector[2]*
                                                                                        pole_vector_distance))

    return pole_vector_position


def clear_objects(root, guide_type):
    """
    TODO: Currently only works with joint objects. Need to generalise more for different object(s)
    Clears our objects under the namespace.
    :param root: namespace root
    :param guide_type: namespace guide type.
    :return:
    """

    ns_path = f"{root}:{guide_type}"

    objects = cmds.namespaceInfo(ns_path, ls=True)

    joints= []

    if objects:
        for _object in objects:
            if cmds.objectType(_object) == 'joint':
                joints.append(_object)

        cmds.delete(joints[0])


