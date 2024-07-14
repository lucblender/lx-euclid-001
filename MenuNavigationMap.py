from ucollections import OrderedDict


def get_menu_navigation_map():
    my_dict = OrderedDict()

    outputs = OrderedDict()

    out = OrderedDict()
    out["data_pointer"] = None
    out["Inverted output"] = {
        "values": ["False", "True"],
        "attribute_name": "inverted_output"
    }
    out["Is Turing Machine"] = {
        "values": ["False", "True"],
        "attribute_name": "is_turing_machine"
    }
    out["Prescaler"] = {
        "values": ["1", "2", "3", "4", "8", "16"],
        "attribute_name": "prescaler_index"
    }
    out["Gate Length"] = {
        "min": 10,
        "max": 2000,
        "steps": 10,
        "attribute_name": "gate_length_ms"
    }
    out["Rand Gate Length"] = {
        "values": ["False", "True"],
        "attribute_name": "randomize_gate_length"
    }

    outputs["Out 0"] = out
    outputs["Out 1"] = out.copy()
    outputs["Out 2"] = out.copy()
    outputs["Out 3"] = out.copy()
    my_dict["Outputs"] = outputs

    cv_dict = {"data_pointer": None,
               "Live action": {
                   "values": ["None", "beats", "pulses", "rotation", "probability"],
                   "attribute_name": "cv_action"
               },
               "Action Rythm": {
                   "values": ["1", "2", "3", "4"],
                   "attribute_name": "cv_action_rythm"
               },
               }
    cv = OrderedDict()
    cv["CV 0"] = cv_dict
    cv["CV 1"] = cv_dict.copy()
    cv["CV 2"] = cv_dict.copy()
    cv["CV 3"] = cv_dict.copy()
    my_dict["CVs"] = cv

    my_dict["Clock"] = OrderedDict({"data_pointer": None,
                                    "Clock source": {
                                        "values": ["Tap btn", "Clock input"],
                                        "attribute_name": "clk_mode"
                                    },
                                    "Clock polarity": {
                                        "values": ["Rising edge", "Falling edge", "Both edges"],
                                        "attribute_name": "clk_polarity"
                                    }
                                    })

    my_dict["Reset"] = OrderedDict({"data_pointer": None,
                                    "Reset polarity": {
                                        "values": ["Rising edge", "Falling edge", "Both edges"],
                                        "attribute_name": "rst_polarity"
                                    }
                                    })
    interface_dict = OrderedDict()
    interface_dict["Encoder"] = {"data_pointer": None,
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
    circle_dict = {"data_pointer": None,
                   "Live action": {
                       "values": ["None", "Rotate Rythm", "Incr/Decr Pulses", "Incr/Decr Probability", "Incr/Decr Gate Length"],
                       "attribute_name": "inner_rotate_action"
                   },
                   "Action Rythm": {
                       "values": ["1", "2", "3", "4", "all"],
                       "attribute_name": "inner_action_rythm"
                   },
                   }
    interface_dict["Inner Circle"] = circle_dict
    interface_dict["Outer Circle"] = circle_dict.copy()

    my_dict["Interface"] = interface_dict

    my_dict["Presets"] = OrderedDict(
        {"data_pointer": None,
         "Save Preset": {
             "values": ["0", "1"],
             "attribute_name": "save_preset_index"
         },
         "Load Preset": {
             "values": ["0", "1"],
             "attribute_name": "load_preset_index"
         },
         })

    my_dict["Display"] = OrderedDict(
        {"data_pointer": None,
         "Rythm link": {
             "values": ["Circle", "Lines"],
             "attribute_name": "display_circle_lines"
         }
         })
    return my_dict
