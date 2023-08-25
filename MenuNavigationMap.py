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
        "Display":OrderedDict(
        {"data_pointer": None,
            "Rythm link": {
                "values": ["Circle", "Lines"],
                "attribute_name": "display_circle_lines"
            }
         })
    })
    return my_dict

