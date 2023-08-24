from collections import OrderedDict

def get_menu_navigation_map():
    my_dict =  OrderedDict({
        "Outputs":OrderedDict(
        {"Out 0": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
            }
        },
            "Out 1": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
            }
        },
            "Out 2": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
            }
        },
            "Out 3": {
            "data_pointer": None,
            "Inverted output": {
                "values": ["False", "True"],
                "attribute_name": "inverted_output"
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
         })
    })
    return my_dict

