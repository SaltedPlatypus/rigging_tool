import maya.standalone 
import maya.cmds as cm

import json
import types
import os
import re

CACHE_FOLDER = os.path.join(__file__, "../../../cache")


def filter_duplicates(set_to_filter):
    """
    Using set() filter for duplicate entries and return.
    :param set_to_filter: list to filter.
    :return: filtered set.
    """

    return set(set_to_filter)


def latest_version(list_of_def_str):
    """
    With a provided list of strings, get the highest string value that ends in an integer.
    Args:
        list_of_def_str(list): Our list of strings to query.

    Returns(str):

    """
    highest_ver = 0
    highest_def = ""
    pattern = re.compile(r'(\d+)$')

    for _def in list_of_def_str:
        match = pattern.search(_def)
        if match:
            ver = int(match.group(1))  # cast to integer
            if ver > highest_ver:
                highest_ver = ver
                highest_def = _def

    return highest_def


def increment_string(incrementing_string):
    """
    With a provided string (with an integer). increment the string integer.
    Args:
        incrementing_string(str): String to increment.

    Returns(str): Modified string.

    """

    match = re.search(r'(\d+)$', incrementing_string)
    if match:
        number_str = match.group(1)
        incremented_num = int(number_str) + 1
        new_num_str = str(incremented_num).zfill(len(number_str))

        new_str_name = incrementing_string[:match.start()] + new_num_str
        return new_str_name
    else:
        raise ValueError("provided string does not contain num character.")


def import_saved_skeleton():
    
    maya.standalone.initialize(name="python")
    path_to_file = ""
    if cm.exists(path_to_file):
        print(f"found file @ {path_to_file}")
        cm.file(path_to_file, open=True, force=True)
        cm.file(path_to_file, i=True)
        """
        We can check later the file name to know where it's at in the process.
        """
        cm.file(rename="saved_skeleton")
        cm.file(save=True, type="mayaBinary")
    
    else: 
        print(f"failed to confirm existance of save file @{path_to_file}")

    maya.standalone.unitialize()

def flatten_list(_list):
    """_summary_

    Args:
        _list (_type_): _description_

    Returns:
        _type_: _description_
    """
    new_list = []
    for member in _list:
        
        if isinstance(member,types.ListType): 
            new_list.extend(member) 
        else: 
            new_list.append(member)
    return new_list


def recursively_search(d, key):
    """
    Recursively search a dictionary (d).
    Args:
        d(dict): Dictionary to recursively search.
        key(str): Key we are querying.

    Returns(str):

    """

    if isinstance(d, dict):
        if key in d:
            return key, d[key]

    for k, v in d.items():
        if isinstance(v, dict):
            result = recursively_search(v, key)
            if result is not None:
                return result

    return None


def dictionary_search(d, *match_keys):
    """
    With any number of provided matching args, query and return matching dictionary data.
    Args:
        d (dictionary) :
        *match_keys (tuple): Expecting String

    Returns(dictionary):

    """

    if not match_keys:
        return d

    results = {}
    for key in match_keys:
        r_k, r_v = recursively_search(d, key)
        results[r_k] = r_v

    return results


def read_definition(_json, *guides, def_type="biped"):
    """
    Not a user input, but a generated key: value pair generated from UI input. E.g:
    If user selects an arm guide.
    Can select multiple and generate.
    Args:
        _json(dict): Dictionary containing extracted json file data.
        *guides(any): *args of any number of strings.
        def_type(str): definition type. For this project, only biped.

    Returns(list): guide data from json. Later we can generalise this function more.

    """

    try:
        values = _json["guides"]
    except KeyError as e:
        raise Exception(f"{e} key does not exist!")

    guide_def = values[def_type]
    guide_data = []

    for guide in guides: # want to be able to input multiple guides but depends on UI functionality.
        # guide_data.append(dictionary_search(guide_def, guide))
        extract_values = dictionary_search(guide_def, guide)
        guide_data.append(extract_values)

    return guide_data



def open_definition(def_name):
    """
    Generic read from json def.
    Args:
        def_name (str): name of definition file to find.

    Returns:
        (dict)
        OR
        (Bool)

    """

    json_file_dir = check_and_return_cache_folder()

    if os.path.exists(json_file_dir):
        for file in os.listdir(json_file_dir):
            if def_name in file:
                maya.utils.executeDeferred('print("found existing .json file.")')
                with open(os.path.join(json_file_dir, file), "r") as json_file:
                    loaded_json = json.load(json_file)
                    return loaded_json
            else:
                maya.utils.executeDeferred('print("{} not found.")'.format(def_name))
                return False
    else:
        print(f"error getting {json_file_dir}")


def check_and_return_cache_folder():
    """
    Check and return cache folder.

    Returns(str): Path to cache folder.

    """

    if not os.path.isdir(CACHE_FOLDER):
        raise FileNotFoundError(f"Cache directory not found: {CACHE_FOLDER}")

    return CACHE_FOLDER

