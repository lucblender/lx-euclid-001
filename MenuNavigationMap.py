from collections import OrderedDict

def get_menu_navigation_map():
    my_dict =  OrderedDict({
        "Outputs":OrderedDict(
        {"Out 0": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
            },
            "Is Turing Machine": {
                "values": ["False", "True"],
                "attribute_name": "is_turing_machine"
            },
            "Prescaler": {
                "values": ["1", "2","3","4","8","16"],
                "attribute_name": "prescaler_index"
            }
        },
            "Out 1": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
            },
            "Is Turing Machine": {
                "values": ["False", "True"],
                "attribute_name": "is_turing_machine"
            },
            "Prescaler": {
                "values": ["1", "2","3","4","8","16"],
                "attribute_name": "prescaler_index"
            }
        },
            "Out 2": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
            },
            "Is Turing Machine": {
                "values": ["False", "True"],
                "attribute_name": "is_turing_machine"
            },
            "Prescaler": {
                "values": ["1", "2","3","4","8","16"],
                "attribute_name": "prescaler_index"
            }
        },
            "Out 3": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
            },
            "Is Turing Machine": {
                "values": ["False", "True"],
                "attribute_name": "is_turing_machine"
            },
            "Prescaler": {
                "values": ["1", "2","3","4","8","16"],
                "attribute_name": "prescaler_index"
            }
        }
        }),
        "Clock":OrderedDict(
        {"data_pointer": None,
            "Clock source": {
                "values": ["Tap btn", "Clock input"],
                "attribute_name": "clk_mode"
            },
             "Clock polarity": {
                "values": ["Rising edge","Falling edge", "Both edges"],
                "attribute_name": "clk_polarity"
            }
         }),
        "Reset":OrderedDict(
        {"data_pointer": None,
            "Reset polarity": {
                "values": ["Rising edge","Falling edge", "Both edges"],
                "attribute_name": "rst_polarity"
            }
         }),
        "Interface":OrderedDict(
            {
                "Encoder":
                {"data_pointer": None,
                 "Long Press": {
                    "values": ["None", "Reset", "Switch Preset"],
                    "attribute_name": "encoder_long_press_action"
                    },
                },
                "Tap Button":
                {"data_pointer": None,
                 "Long Press": {
                    "values": ["None", "Reset", "Switch Preset"],
                    "attribute_name": "tap_long_press_action"
                    },
                },
                "Inner Circle":
                {"data_pointer": None,
                 "Live action": {
                    "values": ["None", "Rotate"],
                    "attribute_name": "inner_rotate_action"
                    },
                 "Action Rythm": {
                    "values": ["1", "2", "3", "4", "all"],
                    "attribute_name": "inner_action_rythm"
                    },
                },
                "Outer Circle":
                {"data_pointer": None,
                 "Live action": {
                    "values": ["None", "Rotate"],
                    "attribute_name": "outer_rotate_action"
                    },
                 "Action Rythm": {
                    "values": ["1", "2", "3", "4", "all"],
                    "attribute_name": "outer_action_rythm"
                    },
                }
            }
        )
        ,
        "Presets":OrderedDict(
        {"data_pointer": None,
        "Save Preset": {
            "values": ["0", "1"],
            "attribute_name": "save_preset_index"
            },
         "Load Preset": {
            "values": ["0", "1"],
            "attribute_name": "load_preset_index"
            },
         }),
        "Display":OrderedDict(
        {"data_pointer": None,
            "Rythm link": {
                "values": ["Circle", "Lines"],
                "attribute_name": "display_circle_lines"
            }
         })
    })
    return my_dict


