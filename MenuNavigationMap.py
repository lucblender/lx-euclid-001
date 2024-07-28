from ucollections import OrderedDict


def get_menu_navigation_map():
    my_dict = OrderedDict()

    outputs = OrderedDict()

    out = OrderedDict()
    out["data_pointer"] = None
    out["Prescaler"] = {
        "values": ["1", "2", "3", "4", "8", "16"],
        "attribute_name": "prescaler_index"
    }
    out["Gate Length"] = {
        "min": 10,
        "max": 250,
        "steps": 10,
        "attribute_name": "gate_length_ms"
    }
    out["Rand Gate Length"] = {
        "values": ["False", "True"],
        "attribute_name": "randomize_gate_length"
    }

    outputs["Out 1"] = out
    outputs["Out 2"] = out.copy()
    outputs["Out 3"] = out.copy()
    outputs["Out 4"] = out.copy()
    my_dict["Outputs"] = outputs

    my_dict["Clock"] = OrderedDict({"data_pointer": None,
                                    "Clock source": {
                                        "values": ["Tap btn", "Clock input"],
                                        "attribute_name": "clk_mode"
                                    }})

    interface_dict = OrderedDict()
    interface_dict["Menu Button"] = {"data_pointer": None,
                                     "Long Press": {
                                         "values": ["None", "Reset", "Switch Preset"],
                                         "attribute_name": "encoder_long_press_action"
                                     },
                                     }
    interface_dict["Tap Button"] = {"data_pointer": None,
                                    "Long Press": {
                                        "values": ["None", "Reset", "Switch Preset"],
                                        "attribute_name": "tap_long_press_action"
                                    },
                                    }
    interface_dict["Touch"] = {"data_pointer": None,
                               "Sensitivity": {
                                   "values": ["Low", "Medium", "High"],
                                   "attribute_name": "touch_sensitivity"
                               },
                               }

    my_dict["Interface"] = interface_dict

    return my_dict
