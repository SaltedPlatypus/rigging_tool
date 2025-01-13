def guide_data():
    """
    Just holds our default guide data.
    :return:
    """

    data = {
        "guides": {
            "biped": {
                "limb": {
                    "arm": {
                        "joint0": {
                            "translateOffsetXYZ": [0.0, 0.0, 0.0],
                            "orientOffsetXYZ": [0.0, 15.0, 0.0],
                            "scaleXYZ": [1.0, 1.0, 1.0]
                        },
                        "joint1": {
                            "translateOffsetXYZ": [5.0, 0.0, 0.0],
                            "orientOffsetXYZ": [0.0, -27.771, 0.0],
                            "scaleXYZ": [1.0, 1.0, 1.0],
                            "parent": "joint0"
                        },
                        "joint2": {
                            "translateOffsetXYZ": [5.0, 0.0, 0.0],
                            "orientOffsetXYZ": [0.0, 0.0, 0.0],
                            "scaleXYZ": [1.0, 1.0, 1.0],
                            "parent": "joint1"
                        }
                    },
                    "leg": {
                        "joint0": {
                            "translateOffsetXYZ": [0.0, 0.0, 0.0],
                            "orientOffsetXYZ": [0.0, 0.0, 0.0],
                            "scaleXYZ": [1.0, 1.0, 1.0]
                        },
                        "joint1": {
                            "translateOffsetXYZ": [0.0, 0.0, 0.0],
                            "orientOffsetXYZ": [0.0, 0.0, 0.0],
                            "scaleXYZ": [1.0, 1.0, 1.0],
                            "parent": "joint0"
                        },
                        "joint2": {
                            "translateOffsetXYZ": [0.0, 0.0, 0.0],
                            "orientOffsetXYZ": [0.0, 0.0, 0.0],
                            "scaleXYZ": [1.0, 1.0, 1.0],
                            "parent": "joint1"
                        }
                    }
                }
            }
        }
    }

    return data
