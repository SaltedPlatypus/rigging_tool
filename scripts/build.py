from maya import cmds
import maya.OpenMaya as om

from Util import utils
from Util import autorig_utils

try:
    from Util import utils
    from Util import  autorig_utils
except Exception as e:
    import sys
    sys.path.append("C:/Users/Thomas Killick/Documents/maya/modules/rigging_tool")
    from Util import utils
    from Util import autorig_utils

def prep_scene(guide_data, root="Guides"):
    """
    Run once per session.
    Args:
        guide_data:
        rigdef:

    Returns:

    """
    cmds.namespace(set=":")
    ns_map = []

    rig_def_ns = autorig_utils.setup_ns_environment()

    for guide in guide_data:
        ns_map.append(list(guide.keys())[0])

    existing_objs = []
    for guide_ns in ns_map:
        found_items = (autorig_utils.search_ns_items(guide_ns))
        for k, v in found_items.items():
            existing_item = om.MFnDagNode(v)
            existing_objs.append(existing_item.name())

    filtered_set = utils.filter_duplicates(existing_objs)
    child_namespaces = []

    for item in filtered_set:
        namespaces = item.split(":")
        if rig_def_ns in namespaces:
            continue
        child_namespaces.append(namespaces[-2])

    filtered_ns = utils.filter_duplicates(child_namespaces)

    for ns in filtered_ns:
        autorig_utils.relocate_ns(src_ns=ns, parent=rig_def_ns, merge=True, force=True)

    # remove any empty namespaces
    for ns in ns_map:
        autorig_utils.create_ns(ns=ns, full_parent_path=f"{root}:{rig_def_ns}")
        autorig_utils.relocate_ns(src_ns=ns, parent=rig_def_ns, merge=False)


# TODO: GENERATES FROM CACHE ONLY
def generate_guide_from_cache(guide_data, root_ns="Guides", rigdef_ns="rigdef_1"):
    """
    (WIP) Takes guide data from the JSON via UI
    Args:
        guide_data:
        root_ns:
        rigdef_ns:

    Returns: A dictionary with a single key: value pair where 'guide' is the type of guide created and 'created_objects'
    is a list of the created object(s) associated with the guide.

    """

    cmds.namespace(set=":")

    ns_path = f"{root_ns}:{rigdef_ns}"

    guide_type_name = list(guide_data.keys())[0]
    guide_type_values = guide_data[guide_type_name]

    matrices = []
    guide_names = []
    # generated_guides = {}

    # in 3.7 dictionaries are ordered.
    for guide, value in guide_type_values.items():
        guide_names.append(guide)
        if cmds.objExists(f"{ns_path}:{guide_type_name}:{guide}"):
            return {}
        if "parent" not in value:
            matrices.insert(0, autorig_utils.write_and_construct_matrix(
                translation=value["translateOffsetXYZ"],
                orientation=value["orientOffsetXYZ"],
                scale=value["scaleXYZ"]
            ))  # in local space
        elif "parent" in value:
            matrices.append(autorig_utils.write_and_construct_matrix(
                translation=value["translateOffsetXYZ"],
                orientation=value["orientOffsetXYZ"],
                scale=value["scaleXYZ"]
            ))  # add next in array/
        else:
            raise Exception(f"'parent' not found in {guide} data.")

    created_objects = []

    # need to add the objects to the namespace.
    cmds.namespace(set=f"{ns_path}:{guide_type_name}")

    index = 0

    for (guide, value), matrix in zip(guide_type_values.items(), matrices):

        matrix_list = [matrix[i] for i in range(16)]

        current_object_name = cmds.spaceLocator(name=guide_names[index])
        created_objects.append(current_object_name)

        if "parent" in value:
            cmds.parent(current_object_name, f"{ns_path}:{guide_type_name}:{value['parent']}")

        cmds.xform(current_object_name, matrix=matrix_list, os=True)

        index += 1

    # generated_guide = {guide_type_name: created_objects}

    return {guide_type_name: created_objects}


def ui_guides(list_of_guide_entries):
    """
    list of our selected guide entries passed from the UI menu.

    :param list_of_guide_entries:
    :return:
    """

    list_of_generated_guides = []  # list of our guides that are generated.

    for selected_guide in list_of_guide_entries:
        list_of_generated_guides.append(generate_guide_from_cache(selected_guide))

    for generated in list_of_generated_guides:
        print(generated)

    return list_of_generated_guides


def build_skeleton(current_guide_data):
    """
    Builds out skeleton (joint chain) from our provided guides data.
    :param current_guide_data: dict
    :return: None
    """
    # main our joints from guides

    cmds.select(clear=True)
    root = "skeleton_def"

    cmds.namespace(set=":")
    if not cmds.namespace(ex=root):
        autorig_utils.set_and_add_ns(set_ns=":", add_ns=root)

    joints = []
    guide_rotators = []

    cmds.select(clear=True)  # clear our current selection

    current_guide_type = list(current_guide_data.keys())[0]  # e.g. "arm"

    print("current: ", current_guide_type)

    autorig_utils.create_ns(ns=current_guide_type, full_parent_path=root)  # create our namespace to contain guides.

    if cmds.namespace(ex=f"{root}:{current_guide_type}"):
        cmds.namespace(set=f"{root}:{current_guide_type}")  # set it as active.

    autorig_utils.clear_objects(f"{root}:{current_guide_type}", joints_only=True)

    for guide_name, guides in current_guide_data.items():
        for i, transforms in enumerate(guides):
            joint_name = transforms[0].split(":")[-1]
            # guide_translation = cmds.xform(transforms[0], q=True, os=True, t=True)
            guide_translation = [cmds.getAttr(f"{transforms[0]}.tx"),
                                 cmds.getAttr(f"{transforms[0]}.ty"), cmds.getAttr(f"{transforms[0]}.tz") ]
            guide_rotation = [cmds.getAttr(f"{transforms[0]}.rx"),
                                 cmds.getAttr(f"{transforms[0]}.ry"), cmds.getAttr(f"{transforms[0]}.rz") ]

            guide_rotators.append(guide_rotation)

            joint = cmds.joint(name=joint_name, p=guide_translation, r=True)

            joints.append(joint)

    for joint, rotator in zip(joints, guide_rotators):
        cmds.joint(joint, e=True, o=rotator)

    # fix orientations
    for joint in joints:
        autorig_utils.fix_joint_orientations(joint)

    # set active namespace back to root skeleton def namespace.
    cmds.namespace(set=f":{root}")


def generate_ik_rig(ns, guide_type, ordered_joints):
    """
    Taking the namesapce, the type of guide e.g.arm and the list of ordereed joints, generate our IK rig.
    :param ns: namespace
    :param guide_type: guide type
    :param ordered_joints: list of ordered joints
    :return: None
    """

    if guide_type != "arm":
        return

    chain_root = ordered_joints[0]
    chain_child = ordered_joints[-1]

    dup_joint = autorig_utils.duplicate_joint(chain_root, name="IK_")  # duplicate the joints to create IK skeleton.

    nested_joints = cmds.listRelatives(dup_joint, allDescendents=True, type="joint") or []

    if len(nested_joints) != 3:
        raise Exception("error generating IK: IK joint chain != 3")

    ik_handle_name = ns+"_IKHandle"
    ik_effector_name = ns+"_IKEffector"

    ik_handle = cmds.ikHandle(
        name=ik_handle_name,
        startJoint=dup_joint,
        endEffector=nested_joints[2],
        solver="ikRPsolver"
    )

    ik_effector = ik_handle[1]
    cmds.rename(ik_effector, ik_effector_name)

    autorig_utils.position_pole_vector(ik_handle, f=False)


def build_rig(ns, guide_type):
    """
    Builds out our rig (full rig).
    :param ns: namespace
    :param guide_type: type of guide.
    :return: None
    """
    # main our control rig from our skeleton.
    items = autorig_utils.search_ns_items(ns)

    deform_joints = []
    for key, value in items.items():
        name = key.split(":")[-1]
        if "joint" in name and cmds.objectType(key) == 'joint':
            deform_joints.append(f"{ns}:{name}")

    # search ns items recursively searches DAG so very unlikely, but to prevent breakage:
    ordered_joints = autorig_utils.reorder_joints(deform_joints)

    generate_ik_rig(ns, guide_type, ordered_joints)


def skin():
    pass


def pose():
    pass

"""new_json = utils.open_definition("guides")

guides_to_generate = utils.read_definition(new_json, "arm") # we actually want read_definition to be read every time we select
# a guide from the UI

prep_scene(guides_to_generate) # prepare our scene for each guide entry

generated_guides = ui_guides(guides_to_generate)

for guide in generated_guides:
    build_skeleton(guide)"""





"""# DATA HANDLING
new_json = utils.open_definition("guides")
data = utils.read_definition(new_json, "arm", "head")"""


"""
# PREPARE NAMESPACES
prep_scene(guide_data)

# CONSTRUCTION
generated_guides = ui_guides(guide_data)

build_skeleton(generated_guides)"""

"""build_rig("skeleton_def:arm", "arm")"""

"""
guide_data is:

 [
    {'arm': 
        {'joint0': 
            {'translateOffsetXYZ': [0.0, 0.0, 0.0], 
            'orientOffsetXYZ': [0.0, 15.0, 0.0], 
            'scaleXYZ': [1.0, 1.0, 1.0]}, 
        'joint1': 
            {'translateOffsetXYZ': [5.0, 0.0, 0.0], 
            'orientOffsetXYZ': [0.0, -27.771, 0.0], 
            'scaleXYZ': [1.0, 1.0, 1.0], 
            'parent': 'joint0'}, 
        'joint2': 
            {'translateOffsetXYZ': [5.0, 0.0, 0.0], 
            'orientOffsetXYZ': [0.0, 0.0, 0.0], 
            'scaleXYZ': [1.0, 1.0, 1.0], 
            'parent': 'joint1'}
        }
    }
]

guide_data[0] refers to the dictionary entry above


"""