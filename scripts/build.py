from maya import cmds
import maya.OpenMaya as om

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

    Returns:

    """

    guide_root = ""

    cmds.namespace(set=":")

    ns_path = f"{root_ns}:{rigdef_ns}"

    guide_type_name = list(guide_data.keys())[0]
    guide_type_values = guide_data[guide_type_name]

    matrices = []
    guide_names = []

    generated_guides = {}

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

    # generated_guides = {guide_type_name: created_objects}
    generated_guides[guide_type_name] = created_objects

    return generated_guides

"""def ui_guides(guide_data):
    # TODO THIS IS JUST TEMPORARY. Replace with UI functions, generate guide only should have relevant guide input.

    generated_guides = []

    arm = guide_data[0]

    generated_guides.append(generate_guide_from_cache(arm))
    # generated_guide = generate_guide(arm)

    return generated_guides"""


def build_skeleton(generated_guide_data):
    """
    Builds out skeleton (joint chain) from our provided guides data.
    :param generated_guide_data: dict
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
    guide = generated_guide_data

    cmds.select(clear=True)
    autorig_utils.create_ns(ns=list(guide.keys())[0], full_parent_path=root)

    if cmds.namespace(ex=f"{root}:{list(guide.keys())[0]}"):
        cmds.namespace(set=f"{root}:{list(guide.keys())[0]}")

    autorig_utils.clear_objects(root, list(generated_guide_data.keys())[0])

    for guide_name, guides in guide.items():
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


"""# DATA HANDLING
new_json = utils.open_definition("guides")
guide_data = utils.read_definition(new_json, "arm", "head")

# PREPARE NAMESPACES
prep_scene(guide_data)

# CONSTRUCTION
generated_guides = ui_guides(guide_data)

build_skeleton(generated_guides)"""

"""build_rig("skeleton_def:arm", "arm")"""