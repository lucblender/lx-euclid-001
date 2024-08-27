from ucollections import OrderedDict


def get_menu_navigation_map():
    my_dict = OrderedDict()

    outputs = OrderedDict()

    out = OrderedDict()
    out["data_pointer"] = None
    out["Algorithm "] = {
        "values": ["Euclidean", "Exponential Eucl.", "Invert Exponential", "Symmetrical Exp."],
        "attribute_name": "algo_index"
    }
    out["Clock Division"] = {
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

    outputs["Ch1"] = out
    outputs["Ch2"] = out.copy()
    outputs["Ch3"] = out.copy()
    outputs["Ch4"] = out.copy()
    my_dict["Channels"] = outputs

    my_dict["Clock source"] = OrderedDict({"data_pointer": None,
                                           "values": ["Internal", "External"],
                                           "attribute_name": "clk_mode"
                                           })

    my_dict["Touch sensitivity"] = {"data_pointer": None,
                                    "values": ["Low", "Medium", "High"],
                                    "attribute_name": "touch_sensitivity"
                                    }

    return my_dict
