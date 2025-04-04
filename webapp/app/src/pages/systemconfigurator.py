import streamlit as st

from ..utils import Page

# import pandas as pd

from adijif.clocks import supported_parts as sp

# from adijif.utils import get_jesd_mode_from_params
import adijif

options_to_skip = ["list_references_available", "d_syspulse"]
parts_to_ignore = ["ad9545", "ad9523_1"]
sp = [p for p in sp if p not in parts_to_ignore]
# Put HMC7044 at the front
sp = [p for p in sp if p != "hmc7044"]
sp.insert(0, "hmc7044")


class SystemConfigurator(Page):
    def __init__(self, state):
        self.state = state

    def write(self):

        st.title("System Configurator")

        vcxo = 125000000

        sys = adijif.system("ad9680", "hmc7044", "xilinx", vcxo)

        # Get Converter clocking requirements
        sys.converter.sample_clock = 1e9
        sys.converter.decimation = 1
        sys.converter.set_quick_configuration_mode(str(0x88))
        sys.converter.K = 32
        sys.Debug_Solver = False

        # Get FPGA clocking requirements
        sys.fpga.setup_by_dev_kit_name("zc706")
        sys.fpga.force_qpll = 1

        cfg = sys.solve()

        # pprint.pprint(cfg)

        # print("Clock config:")
        # pprint.pprint(cfg["clock"])

        # print("Converter config:")
        # pprint.pprint(cfg["converter"])

        print("FPGA config:")
        # pprint.pprint(cfg["fpga_AD9680"])

        # print("JESD config:")
        # pprint.pprint(cfg["jesd_AD9680"])

        data = sys.draw(cfg)

        st.image(data, use_container_width=True)

        settings, diagram = st.columns(2)

        with settings:
            st.header("Settings")

        with diagram:
            st.header("Diagram")

            with st.container(border=True):
                # st.markdown(file)
                print(data)
                st.image(data, use_container_width=True)
