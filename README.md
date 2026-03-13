# CLEARS-EU_public
The CLEARS-EU model estimates national-level adoption pathways for residential battery storage across 25 EU countries using a two-stage framework that integrates economic evaluation with diffusion dynamics (Hartvig, 2025; Hartvig & Szabó, 2025). In the first stage, the model calculates the net present value (NPV) of investing in PV-connected residential battery systems for heterogeneous households, accounting for region-specific load profiles, consumption patterns, and solar radiation characteristics. In the second stage, potential adopters identified by the NPV analysis are incorporated into Bass diffusion models to simulate cumulative adoption trajectories, capturing non-financial drivers and generating S-shaped growth curves.

In this public version of the model, certain proprietary data, specifically historical residential battery and rooftop PV installations, system sizes, and total capacities provided by SolarPower Europe, are not included. Consequently, historical capacities and installations are assumed to be zero, and dummy data are used for PV and battery sizes.

The model can be executed with three distinct battery operation strategies, configurable in the settings.ini file:
1. baseline – batteries are used solely for self-consumption;
2. dynamic – batteries are used solely for self-consumption, hourly electricty tariffs;
3. flex – household can lease some of their battery capacities, charging them when the national load is below the expected daily average and discharging them when it exceeds this level;
4. peak – batteries can discharge electricity to the grid during predefined peak hours.
