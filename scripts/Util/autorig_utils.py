from maya import cmds
import maya.OpenMaya as om
import maya.utils

from itertools import chain

# from . import utils
# from . import ops

try:
    from . import utils
    from . import ops
except Exception as e:
    import sys
    sys.path.append("C:/Users/Thomas Killick/Documents/maya/modules/rigging_tool")
    from scripts.Util import utils
    from scripts.Util import ops


def obj_exists(_object):
    """
    Query if object exists
    :param _object:
    :return:
    """

    if not cmds.objExists(_object):
        raise Exception (f"Queried object: {_object} does not exist!")


def is_transform(obj):
    """
    Check if obj is a valid transform.
    :param obj:
    :return:
    """
    # Check object exists
    if not cmds.objExists(obj): return False

    mObject = getMObject(obj)
    if not mObject.hasFn(om.MFn.kTransform):
        return False

    return True


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


def get_joints_between(start_joint, end_joint=None):
    """

    :param start_joint:
    :param prefix:
    :param end_joint:
    :param parent:
    :return:
    """

    obj_exists(start_joint)
    obj_exists(end_joint)

    if start_joint == end_joint:  # length of 1.
        return start_joint

    relatives = cmds.listRelatives(start_joint, ad=True)
    filter_joints = cmds.ls(relatives, type="joint")

    if not filter_joints.count(end_joint):
        raise Exception(f'End joint: {end_joint} is not a descendant of start joint {start_joint}')

    jnt_list = [end_joint]

    while(jnt_list[-1] != start_joint):
        parent_joint = cmds.listRelatives(jnt_list[-1], p=True, pa=True)
        if not parent_joint:
            raise Exception(f"Returned root joint when searching for {start_joint}.")
        jnt_list.append(parent_joint[0])

    jnt_list.reverse()

    return jnt_list


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
        target_mat = ops.buildRotation(aim_vector, up_vector=up_vector,
                                       aim_axis=aim_axis, up_axis=up_axis)


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


    if cmds.listConnections(ik+'.ikSolver', s=True, d=False)[0] != f'{ik}ikRPsolver':
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


def get_end_object(current_object, joints_only=False):
    """
    Check if current joint is the top joint in a chain, then from that, find the end joint.
    :param current_object:
    :return:
    """

    end_object = None
    if joints_only:
        relatives = cmds.listRelatives(current_object, ap=True, type="joint")
    else:
        relatives = cmds.listRelatives(current_object, ap=True)

    if not relatives:
        start_object = current_object
        next_object = start_object

        while(next_object):

            child_list = cmds.listRelatives(next_object, c=True) or []  # return empty list

            if joints_only:
                child_objects = cmds.ls(child_list, type="joint") or []
            else:
                child_objects = cmds.ls(child_list, type="joint") + \
                                cmds.ls(child_list, type="transform") or []

            if child_objects:
                next_object = child_objects[0]
            else:
                end_object = next_object
                next_object = None

        return end_object

    else:

        return []


def traverse_hierarchy(current_object, ascend=False, joints_only=False):
    """
    Must be called in a loop, we yield the current joint in the traversal.
    :param current_object:
    :param ascend:
    :return:
    """

    objects_to_return = []

    if not cmds.objExists(current_object):
        return objects_to_return

    if ascend:
        current_object = get_end_object(current_object)

        # Initialize the object to start the loop
        next_object = current_object

        while next_object:
            parent_list = cmds.listRelatives(next_object, p=True) or []

            if joints_only:
                parent_objects = cmds.ls(parent_list, type="joint") or []
            else:
                parent_objects = list(chain(cmds.ls(parent_list, type="joint"),
                           cmds.ls(parent_list, type="transform")))

            if parent_objects:
                objects_to_return.append(next_object)
                next_object = parent_objects[0]
            else:
                objects_to_return.append(next_object)
                next_object = None

    else:
        objects_to_return.append(current_object)

    return objects_to_return


def clear_objects(name_space, joints_only=False):
    """
    :param name_space: Target namespace to clear object(s) under.
    :return: None.
    """

    objects_to_clear = cmds.namespaceInfo(name_space, ls=True)

    print_list = []
    if objects_to_clear:
        for _object in objects_to_clear:
            target_objects = traverse_hierarchy(_object, ascend=True, joints_only=joints_only)
            for t_object in target_objects:
                print_list.append(t_object)
                cmds.delete(t_object)

    cmds.evalDeferred(lambda: print(f"Deleted {print_list} object(s)"))


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

    duplicated_joint = cmds.duplicate(joint, po=True, n=f"d_{joint}")[0]  # just duplicate parent.

    if name:
        duplicated_joint = cmds.rename(duplicated_joint, name)

    attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v', 'radius']
    for attr in attributes:
        cmds.setAttr(duplicated_joint+"."+attr, l=False, cb=True)

    return duplicated_joint


def chain_duplication(start_joint,
                          prefix=None,
                          end_joint=None,
                          parent=None):
    """

    :param start_joint:
    :param prefix:
    :param end_joint:
    :param parent:
    :return:
    """

    duplicate_chain = []

    obj_exists(start_joint)
    if end_joint:
        obj_exists(end_joint)

    if parent:
        obj_exists(parent)
        if not is_transform(parent):
            raise Exception(f'Parent object[{parent}] is not a valid transform!')

    if not end_joint:
        end_joint = get_end_object(start_joint)

    joints = get_joints_between(start_joint, end_joint)

    for i, joint in enumerate(joints):
        name = None

        if prefix:
            string_end = joint.split(":")[-1]
            name = prefix+string_end

        jnt = duplicate_joint(joint, name)  # remove name for now.

        if not i:
            if not parent:
                if cmds.listRelatives(jnt, p=True):
                    try:
                        cmds.parent(jnt, w=True)
                    except Exception as e:
                        pass
            else:
                try:
                    cmds.parent(jnt, parent)
                except Exception as e:
                    pass
        else:
            try:
                cmds.parent(jnt, duplicate_chain[-1])

                # keep child transform consistent to parent scaling.
                if not cmds.isConnected(duplicate_chain[-1]+".scale", jnt+".inverseScale"):
                    cmds.connectAttr(duplicate_chain[-1]+".scale", jnt+".inverseScale", f=True)
            except Exception as e:
                raise Exception("Duplication error. Exception: " + str(e))

        duplicate_chain.append(jnt)

    return duplicate_chain


"""chain = cmds.ls(type="joint")
print(chain)

duplicates = chain_duplication(chain[0], prefix="ik_")

print(duplicates)"""