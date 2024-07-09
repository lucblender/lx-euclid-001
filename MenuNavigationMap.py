from ucollections import OrderedDict
    
def get_menu_navigation_map():
    my_dict =  OrderedDict()
 
    outputs = OrderedDict()

    out0 = OrderedDict()
    out0["data_pointer"] = None
    out0["Inverted output"] = {
                                "values": ["False", "True"],
                                "attribute_name": "inverted_output"
                            }
    out0["Is Turing Machine"] = {
                                "values": ["False", "True"],
                                "attribute_name": "is_turing_machine"
                            }
    out0["Prescaler"] = {
                        "values": ["1", "2","3","4","8","16"],
                        "attribute_name": "prescaler_index"
                    }
    out0["Gate Length"] = {
                            "min": 10,
                            "max": 2000,
                            "steps": 10,
                            "attribute_name": "gate_length_ms"
                        }
    out0["Rand Gate Length"] = {
                                "values": ["False", "True"],
                                "attribute_name": "randomize_gate_length"
                            }


    out1 = OrderedDict()
    out1["data_pointer"] = None
    out1["Inverted output"] = {
                                "values": ["False", "True"],
                                "attribute_name": "inverted_output"
                            }
    out1["Is Turing Machine"] = {
                                "values": ["False", "True"],
                                "attribute_name": "is_turing_machine"
                            }
    out1["Prescaler"] = {
                        "values": ["1", "2","3","4","8","16"],
                        "attribute_name": "prescaler_index"
                    }
    out1["Gate Length"] = {
                            "min": 10,
                            "max": 2000,
                            "steps": 10,
                            "attribute_name": "gate_length_ms"
                        }
    out1["Rand Gate Length"] = {
                                "values": ["False", "True"],
                                "attribute_name": "randomize_gate_length"
                            }


    out2 = OrderedDict()
    out2["data_pointer"] = None
    out2["Inverted output"] = {
                                "values": ["False", "True"],
                                "attribute_name": "inverted_output"
                            }
    out2["Is Turing Machine"] = {
                                "values": ["False", "True"],
                                "attribute_name": "is_turing_machine"
                            }
    out2["Prescaler"] = {
                        "values": ["1", "2","3","4","8","16"],
                        "attribute_name": "prescaler_index"
                    }
    out2["Gate Length"] = {
                            "min": 10,
                            "max": 2000,
                            "steps": 10,
                            "attribute_name": "gate_length_ms"
                        }
    out2["Rand Gate Length"] = {
                                "values": ["False", "True"],
                                "attribute_name": "randomize_gate_length"
                            }


    out3 = OrderedDict()
    out3["data_pointer"] = None
    out3["Inverted output"] = {
                                "values": ["False", "True"],
                                "attribute_name": "inverted_output"
                            }
    out3["Is Turing Machine"] = {
                                "values": ["False", "True"],
                                "attribute_name": "is_turing_machine"
                            }
    out3["Prescaler"] = {
                        "values": ["1", "2","3","4","8","16"],
                        "attribute_name": "prescaler_index"
                    }
    out3["Gate Length"] = {
                            "min": 10,
                            "max": 2000,
                            "steps": 10,
                            "attribute_name": "gate_length_ms"
                        }
    out3["Rand Gate Length"] = {
                                "values": ["False", "True"],
                                "attribute_name": "randomize_gate_length"
                            }

    outputs["Out 0"] = out0
    outputs["Out 1"] = out1
    outputs["Out 2"] = out2
    outputs["Out 3"] = out3
    my_dict["Outputs"] = outputs

    my_dict["Clock"] = OrderedDict({"data_pointer": None,
                                    "Clock source": {
                                        "values": ["Tap btn", "Clock input"],
                                        "attribute_name": "clk_mode"
                                    },
                                     "Clock polarity": {
                                        "values": ["Rising edge","Falling edge", "Both edges"],
                                        "attribute_name": "clk_polarity"
                                    }
                                 })

    my_dict["Reset"] = OrderedDict({"data_pointer": None,
                                    "Reset polarity": {
                                        "values": ["Rising edge","Falling edge", "Both edges"],
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
    interface_dict["Touch"] ={"data_pointer": None,
                             "Sensitivity": {
                                "values": ["Low", "Medium", "High"],
                                "attribute_name": "touch_sensitivity"
                                },
                            } 
    interface_dict["Inner Circle"] = {"data_pointer": None,
                                     "Live action": {
                                        "values": ["None", "Rotate Rythm", "Incr/Decr Pulses", "Incr/Decr Probability", "Incr/Decr Gate Length"],
                                        "attribute_name": "inner_rotate_action"
                                        },
                                     "Action Rythm": {
                                        "values": ["1", "2", "3", "4", "all"],
                                        "attribute_name": "inner_action_rythm"
                                        },
                                    }
    interface_dict["Outer Circle"] = {"data_pointer": None,
                                     "Live action": {
                                        "values": ["None", "Rotate Rythm", "Incr/Decr Pulses", "Incr/Decr Probability", "Incr/Decr Gate Length"],
                                        "attribute_name": "outer_rotate_action"
                                        },
                                     "Action Rythm": {
                                        "values": ["1", "2", "3", "4", "all"],
                                        "attribute_name": "outer_action_rythm"
                                        },
                                    }

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
