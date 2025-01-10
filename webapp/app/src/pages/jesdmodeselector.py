import streamlit as st
from ..utils import Page

import pandas as pd

from adijif.converters import supported_parts as sp
from adijif.utils import get_jesd_mode_from_params
import adijif

from .helpers.jesd import get_jesd_controls, get_valid_jesd_modes

options_to_skip = ["global_index", "decimations"]


class JESDModeSelector(Page):
    def __init__(self, state):
        self.state = state
        self.part_images = {}

    def write(self):

        # Get supported parts that have quick_configuration_modes
        supported_parts_filtered = []
        for part in sp:
            try:
                converter = eval(f"adijif.{part}()")
                qsm = converter.quick_configuration_modes
                supported_parts_filtered.append(part)
            except:
                pass
        supported_parts = supported_parts_filtered

        st.title("JESD204 Mode Selector")

        sb = st.selectbox(
            label="Select a part",
            options=supported_parts,
            format_func=lambda x: x.upper(),
        )

        converter = eval(f"adijif.{sb}()")

        ## Show diagram
        with st.expander(label="Diagram", expanded=True):
            if sb not in self.part_images:
                # Generate image
                from .helpers.drawers import draw_ad9680

                self.part_images[sb] = draw_ad9680()
                # FIXME: State is not being saved

            st.image(self.part_images[sb], use_container_width=True)

        ## Shared Configuration
        with st.expander("Shared Configuration", expanded=True):
            decimation = 1
            if converter.datapath:
                if hasattr(converter.datapath, "cddc_decimations_available"):
                    print("Here")
                    options = converter.datapath.cddc_decimations_available
                    cddc_decimation = st.selectbox(
                        "CDDC Decimation", options=options, format_func=lambda x: str(x)
                    )
                    decimation = cddc_decimation
                    v = len(converter.datapath.cddc_decimations)
                    converter.datapath.cddc_decimations = [cddc_decimation] * v
                if hasattr(converter.datapath, "fddc_decimations_available"):
                    options = converter.datapath.fddc_decimations_available
                    fddc_decimation = st.selectbox(
                        "FDDC Decimation", options=options, format_func=lambda x: str(x)
                    )
                    decimation *= fddc_decimation
                    v = len(converter.datapath.fddc_decimations)
                    converter.datapath.fddc_decimations = [fddc_decimation] * v
            elif hasattr(converter, "decimation_available"):
                decimation = st.selectbox(
                    "Decimation",
                    options=converter.decimation_available,
                    format_func=lambda x: str(x),
                )
                decimation = int(decimation)
                converter.decimation = decimation

            converter_rate = st.number_input("Converter Rate (Hz)", value=1e9)
            converter.sample_clock = converter_rate / decimation

        ## Derived settings
        dict_data = {
            "Derived Setting": ["Sample Rate (MSPS)"],
            "Value": [converter.sample_clock / 1e6],
        }
        df = pd.DataFrame.from_dict(dict_data)
        st.dataframe(df, hide_index=True, use_container_width=True)

        cols = st.columns(2, border=True)

        ## JESD204 Configuration Inputs
        options, all_modes = get_jesd_controls(converter)
        selections = {}

        with cols[0]:
            st.subheader("Configuration")

            for option in options:
                selections[option] = st.multiselect(option, options[option])

        ## Output table of valid modes and calculate clocks
        selections = {k: v for k, v in selections.items() if v != []}
        modes_all_info, found_modes = get_valid_jesd_modes(
            converter, all_modes, selections
        )

        with cols[1]:
            st.subheader("JESD204 Modes")

            if found_modes:
                # Create formatted table of modes

                # Convert to DataFrame so we can change orientation
                df = pd.DataFrame(modes_all_info)

                show_valid = st.toggle("Show only valid modes", value=True)
                if show_valid:
                    df = df[df["Valid"] == "Yes"]
                    df = df.drop(columns=["Valid"])

                # Create new index column and move mode to separate column
                df["Mode"] = df.index
                df = df.reset_index(drop=True)
                # Make mode first column
                cols = df.columns.tolist()
                cols = cols[-1:] + cols[:-1]
                df = df[cols]

                # Change jesd_class column name to be JESD204 Class
                df = df.rename(columns={"jesd_class": "JESD204 Class"})
                df = df.rename(columns={"Mode": "Quickset Mode"})

                # Change data in jesd_class column to be more human readable
                df["JESD204 Class"] = df["JESD204 Class"].replace(
                    {"jesd204b": "204B", "jesd204c": "204C"}
                )

                to_disable = df.columns
                height = len(df) * 50
                de = st.data_editor(
                    df,
                    use_container_width=True,
                    disabled=to_disable,
                    hide_index=True,
                    height=height,
                )

            else:
                st.write("No modes found")
