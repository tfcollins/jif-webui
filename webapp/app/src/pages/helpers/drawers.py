import adijif as jif
import os


def draw_ad9680():

    if os.path.exists("ad9680_example.svg"):
        return "ad9680_example.svg"

    adc = jif.ad9680()

    # Check static
    adc.validate_config()

    required_clocks = adc.get_required_clocks()
    required_clock_names = adc.get_required_clock_names()

    # Add generic clock sources for solver
    clks = []
    for clock, name in zip(required_clocks, required_clock_names):
        clk = jif.types.arb_source(name)
        adc._add_equation(clk(adc.model) == clock)
        clks.append(clk)

    # Solve
    solution = adc.model.solve(LogVerbosity="Quiet")
    settings = adc.get_config(solution)

    # Get clock values
    clock_values = {}
    for clk in clks:
        clock_values.update(clk.get_config(solution))
    settings["clocks"] = clock_values

    # print(settings)
    # print(dir(adc))
    adc.show_rates = False
    image_data = adc.draw(settings["clocks"])

    # return image_data

    with open("ad9680_example.svg", "w") as f:
        f.write(image_data)

    return "ad9680_example.svg"
