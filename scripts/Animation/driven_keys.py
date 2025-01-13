import pymel.core as pm
import json
import os

json_cache_directory = "path/to/your/cache"

# TODO: Convert from Python 2

class AnimCurve:

    def __init__(self, object):
        self.object = object
        self.in_connections = []
        self.out_connections = []
        self.animCurve_data = {}

    def update_input_connections(self, parent=False):
        """
        Updates our input connection attributes. If parent is false, update with the attribute channel only.
        If parent is true, updates input_connection(s) with the parent node(s) only.
        Args:
            parent(bool): parent flag.
        Returns:
        """
        # clean our in connections should we call this again.
        self.in_connections = []

        if not parent:

            in_connections = self.object.input.listConnections(plugs=True)
        else:

            in_connections = self.object.input.listConnections()

        if not in_connections:
            pm.displayWarning("No incoming connections for animCurve({})".format(self.object))
        for attr in in_connections:
            attribute = attr.name()
            self.in_connections.append(attribute)

        return self.in_connections

    def update_output_connections(self, parent=False):
        """
        Updates our output connection attributes. If parent is false, update with the attribute channel only.
        If parent is true, updates out_connection(s) with the parent node(s) only.
        Args:
            parent(bool): parent flag.
        Returns:
        """
        # clean our out_connections should we call this again.
        self.out_connections = []

        if not parent:
            out_connections = self.object.output.listConnections(plugs=True)
        else:
            out_connections = self.object.output.listConnections()

        if not out_connections:
            pm.displayWarning("No outgoing connections for animCurve({})".format(self.object))

        for attr in out_connections:
            attribute = attr.name()
            self.out_connections.append(attribute)

        return self.out_connections

    def update_curve_data(self):

        # clean out animCurve_data should we call update again.
        self.animCurve_data = {}

        if self.object.numKeys() != 0:

            num_keys = pm.keyframe(self.object.name(), q=True, kc=True)
            for i in range(num_keys):

                v = pm.keyframe(self.object.name(), index=[i, i], q=True, vc=True)

                t = pm.keyframe(self.object.name(), index=[i, i], q=True, fc=True)

                ix = pm.keyTangent(self.object.name(), index=[i, i], q=True, ix=True)[0]
                # our outgoing x tangent value
                ox = pm.keyTangent(self.object.name(), index=[i, i], q=True, ox=True)[0]
                # our incoming y tangent value
                iy = pm.keyTangent(self.object.name(), index=[i, i], q=True, iy=True)[0]
                # our outgoing y tangent value
                oy = pm.keyTangent(self.object.name(), index=[i, i], q=True, oy=True)[0]

                tangentData = {
                    "ix": ix,
                    "ox": ox,
                    "iy": iy,
                    "oy": oy
                }

                # query to find our Tangent Types
                inTangentType = pm.keyTangent(self.object.name(), index=[i, i], q=True, inTangentType=True)[0]
                outTangentType = pm.keyTangent(self.object.name(), index=[i, i], q=True, outTangentType=True)[0]

                current_keyframe_data = {
                    "value": v,
                    "driver_val": t,
                    "tangent_data": tangentData,
                    "inTangent_type": inTangentType,
                    "outTangent_type": outTangentType
                }
                self.animCurve_data["{}".format(i)] = current_keyframe_data

            return self.animCurve_data

        else:
            pm.displayWarning("No keys found on object")


def generate_animcurve_objects():
    """
    generates our driver/driven animCurve objects (not the animCurves themselves).
    Returns: list of our new AnimationCurve object(s).
    """

    # generate our curve objects - need to add extra check later dependin on user chosen.
    print("\nGenerating AnimCurve object(s)")
    curve_objs = [AnimCurve(pm.PyNode(c)) for c in pm.ls(type="animCurve")]
    print("\nGenerated AnimCurve object(s)")
    if not curve_objs:
        pm.displayWarning("No accessible of type animCurve in scene")

    return curve_objs


def write_to_json(driven_animCurves):
    """
    Write to our json files the data we have.
    Args:
        driven_animCurves(list): list of our animCurve object(s).
    Returns:
    """

    data = {}
    for obj in driven_animCurves:

        obj_data = {
            "in_connection_attr": obj.update_input_connections(),
            "out_connection_attr": obj.update_output_connections(),
            "curve_data": obj.update_curve_data()
        }

        data[obj.object.name()] = obj_data

    json_object = json.dumps(data, indent=4)
    print("\nAttempting to write to JSON file...")
    try:
        with open(json_cache_directory + "driven_data.json", "w") as outfile:
            outfile.write(json_object)
    except IOError as e:  # maybe change to a raise error instead.
        pm.displayWarning("Unable to create JSON file. Check supplied directory is correct.")

    print("\nJSON file successfully written to.")


def print_message(message):
    """
    Python2 does not take print as an iterable.
    Args:
        message(str): message to pass.
    Returns: None
    """

    print(message)


def process_curve_data(key, value, data_checks):
    """
    A function that is called in a lambda operation for processing nested curve data. A bit neater than
    using multiple elif pass statements.
    Args:
        key: The curve_data key.
        value: A dictionary of all curve data.
        data_checks(tuple): A passed Tuple of our required curve data.
    Returns:
    """

    counter = 0  # a counter for number of data entries found.
    print_message(key + " curve data found.\n")  # our curve data is found.

    for curve_key, curve_val in value.items():
        for curve_data in data_checks:  # we need to make sure all our curve requirements are met.
            if curve_data in curve_val:
                for k, v in curve_val.items():
                    try:
                        if isinstance(v, dict):
                            for k_1, v_1 in v.items():  # some JSON data has an additional nest layer.
                                if v_1 is None:
                                    print ("\nWarning: {} has a value of None.".format(k_1))
                        elif isinstance(v, list):
                            for i in v:
                                if i is None:
                                    print ("\nWarning: {} has a value of None.".format(i))
                    except UnicodeError as e:
                        print_message("\nNot nested.".format(k))

                continue
            else:
                print_message("invalid {} curve data entry found\n".format(curve_data))

        counter += 1  # tells us how many keyframes we found in curve data.

    print_message("Found " + str(counter) + " keyframe(s).")


def check_JSON_data(json_data):
    """
    Checking to make sure read JSON data meets required format. Breaks data down to make sure if issues arise from
    data that we can pinpoint where in the data.
    Args:
        json_data(JSON): Our Json file.
    Returns: None
    """

    data_checks = ("tangent_data", "driver_val", "inTangent_type", "value", "outTangent_type")

    key_checks = {
        "in_connection_attr": lambda k: print_message(k + " in_connection found.\n"),
        "out_connection_attr": lambda k: print_message(k + " out_connection found.\n"),
        "curve_data": lambda k, v: process_curve_data(k, v, data_checks),
    }

    for key, value in json_data.items():
        if "driven" in key.lower():
            for attribute_key, attribute_val in value.items():
                # if attribute key name in key_checks dictionary, get the attribute key,val pair and pass data to
                # lambda call.
                if attribute_key in key_checks:
                    if attribute_key == "curve_data":
                        key_checks[attribute_key](key, attribute_val)
                    else:
                        key_checks[attribute_key](key)
                else:
                    print_message(key + " incorrect data entry {} found, check naming".format(attribute_key))

        print("\n-----------------------------------------------\n")

    print ("\n***********************CHECK COMPLETE************************\n")


# [EXPERIMENTAL]
def remove_existing_curves(animCurve_itr, existing_curves):
    """
    Right now, safer to remove existing curves and then create new ones. Later on this can be modified
    to take into account existing curves.
    :param animCurve_itr: The curve at check
    :param existing_curves: The curve to check
    :return:
    """

    # later on when we refactor to add checks in for specific scene object(s), we need a check here.
    # as of now, we want to overwrite regardless of existence or not. This check might be useful later.

    for c in existing_curves:
        if animCurve_itr in c:
            print("\nanimCurve %s exists\n") % c
            pm.delete(c) # disconnect. Could add option to delete later.
            return c
        else:
            print("\nanimCurve does not exist, building...\n")

def build_from_json():
    """
     Read our Json file and build back our animation object logic. (This will need to refactored later as
     it's currently uses variables integrated within this script which should be split out later.
     Returns(list): Our list of re-built animCurve object(s).

    :return:
    """
    print("\n******************************\n")
    print("\nAttempting to read JSON file...\n")

    if os.path.isfile(json_cache_directory + "driven_data.json"):
        with open(json_cache_directory + "driven_data.json") as f:  # replace this bit with something more slick
            json_data = json.load(f)
    else:
        raise Exception("The JSON files does not exist")

    check_JSON_data(json_data)  # check our JSON data.

    num_entries = len(json_data)
    print("Successfully read JSON file. \nNumber of entries: %s" % num_entries)

    list_of_anim_curves = []
    for key, value in json_data.items():

        # replace with delete curves function
        existing_curve = pm.ls(key, type="animCurve")
        if existing_curve:
            list_of_anim_curves.insert(0, AnimCurve(pm.PyNode(key, type="animCurve")))
        else:
            anim_curve_node = pm.createNode("animCurveUA", n=key)
            list_of_anim_curves.insert(0, AnimCurve(anim_curve_node))

        # list_of_anim_curves.insert(0, AnimCurve(pm.PyNode(key, type="animCurve"))) # we call our AnimCurve class.
        # if same-name curves already exist in scene it will not create duplicates.
        current_item = list_of_anim_curves[0]
        current_item.object.name(key)

        for i, v in value.items():
            if "out_connection_attr" in i:
                for x in v:
                    current_item.out_connections.append(x)

            elif "in_connection_attr" in i:
                for x in v:
                    current_item.in_connections.append(x)
            else:
                current_item.animCurve_data = v

    return list_of_anim_curves


def generate_connections(list_of_animCurves):
    """
    This is our main function that generates or re-establishes connection.
    Args:
        list_of_animCurves(list): list containing our AnimCurve class objects and all parsed JSON data.
    Returns: None
    """

    print("\nGenerating Connections...")
    # make a check data function? (Checks if everything is valid
    existing_curves = [c.name() for c in pm.ls(type="animCurve")]

    # NOTE: PyNode(curve) does not actually create a new PyNode if one exists of the same name.
    # Change check method, if PyNode actually already exists, try below, but catch cmds.warning already exists.

    for anim_curve in list_of_animCurves:
        # check if we have any existing curves.
        # matched_curve = check_anim_curves(anim_curve.object.name(), existing_curves) # for testing don't execute

        # get JSON extracted in_connection
        # Connect input attribute to animCurve input.
        for i in anim_curve.in_connections:
            input_attr = pm.PyNode(i)
            # check connections
            if not pm.isConnected(input_attr, anim_curve.object.input):
                input_attr >> anim_curve.object.input
            else:
                pm.displayWarning("Connection already exists: {} -> {}.input".format(input_attr, anim_curve.object))
                print("\nConnection already exists: {} -> {}.input".format(input_attr, anim_curve.object))

        for o in anim_curve.out_connections:
            output_attr = pm.PyNode(o)
            # check connections
            if not pm.isConnected(anim_curve.object.output, output_attr):
                anim_curve.object.output >> output_attr
            else:
                pm.displayWarning("Connection already exists: {} -> {}.output".format(anim_curve.object, output_attr))
                print("\nConnection already exists: {} -> {}.output".format(anim_curve.object, output_attr))

        for key, value in anim_curve.animCurve_data.items():

            # over curve data from our new PyNode animCurve object(s).
            driver_val = value["driver_val"][0]
            y_value = value["value"][0]
            i_tt = value["inTangent_type"]
            o_tt = value["outTangent_type"]

            iy = None
            ix = None
            oy = None
            ox = None

            tan_dict = value["tangent_data"]
            for tan_key, tan_val in tan_dict.items():
                iy = tan_dict["iy"]
                ix = tan_dict["ix"]
                oy = tan_dict["oy"]
                ox = tan_dict["ox"]

            pm.setKeyframe(anim_curve.object, float=driver_val, value=y_value, itt=i_tt, ott=o_tt)
            pm.keyTangent(anim_curve.object, ix=ix, iy=iy, oy=oy, ox=ox, a=True)