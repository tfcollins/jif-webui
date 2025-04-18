import copy

from adijif.utils import get_jesd_mode_from_params


def get_jesd_controls(converter):

    options_to_skip = ["global_index", "decimations"]

    # Derive configurable jesd settings for specific converter based on mode table
    all_modes = converter.quick_configuration_modes
    all_modes = copy.deepcopy(all_modes)
    subclasses = list(all_modes.keys())

    mode_knobs = None

    for subclass in subclasses:
        # Pick first mode of subclass and extract settings
        ks = all_modes[subclass].keys()
        ks = list(ks)
        if len(ks) == 0:
            # print(f"No modes found for subclass {subclass}")
            continue
        first_mode = list(all_modes[subclass].keys())[0]
        mode_settings = all_modes[subclass][first_mode].keys()
        mode_settings = sorted(mode_settings)
        if not mode_knobs:
            mode_knobs = mode_settings
            continue

        # Compare settings in other subclasses to make sure they are the same
        if mode_settings != mode_knobs:
            differences = set(mode_settings) ^ set(mode_knobs)
            print(
                f"Mode settings are not consistent across all subclasses: {differences}"
            )
            raise Exception("Mode settings are not consistent across all subclasses")

    # Parse all options for each control across modes
    options = {}
    for setting in mode_knobs:
        if setting in options_to_skip:
            continue
        options[setting] = []
        for subclass in subclasses:
            for mode in all_modes[subclass]:
                data = all_modes[subclass][mode][setting]
                if type(data) == list:
                    print(f"Skipping list data for {setting}")
                    continue
                options[setting].append(data)

    # Make sure options only contain unique values
    for option in options:
        options[option] = list(set(options[option]))

    return options, all_modes


def get_valid_jesd_modes(converter, all_modes, selections):

    from pprint import pprint

    modes_all_info = {}

    try:
        found_modes = get_jesd_mode_from_params(converter, **selections)

    except:
        print("No modes found")
        found_modes = None
        return modes_all_info, found_modes

    options_to_skip = ["global_index", "decimations"]

    # Get remaining mode parameters
    modes_all_info = []
    for mode in found_modes:
        jesd_cfg = all_modes[mode["jesd_class"]][mode["mode"]]
        jesd_cfg["mode"] = mode["mode"]
        jesd_cfg["jesd_class"] = mode["jesd_class"]

        # Remove options to skip
        for option in options_to_skip:
            jesd_cfg.pop(option, None)

        modes_all_info.append(jesd_cfg)

    # For each mode calculate the clocks and if valid
    for mode in modes_all_info:
        rate = converter.sample_clock
        # print("A", converter.sample_clock)
        converter.set_quick_configuration_mode(mode["mode"], mode["jesd_class"])
        # print("B", converter.sample_clock)
        print("BUG")
        converter.sample_clock = rate

        clocks = {
            "Sample Rate (MSPS)": converter.sample_clock / 1e6,
            "Lane Rate (GSPS)": converter.bit_clock / 1e9,
        }

        for clock in clocks:
            mode[clock] = clocks[clock]

        try:
            converter.validate_config()
            mode["Valid"] = "Yes"
        except Exception as e:
            # print(e)
            mode["Valid"] = "No"

    # from pprint import pprint
    # pprint(modes_all_info)

    return modes_all_info, found_modes
