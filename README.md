# WebSnapse Stress Test

This is the repository holding the systems in JSON (for WebSnapse v3/Reloaded) format
and in XML format (for WebSnapse v2) with increasing neuron count for testing:
- Runtime for computing the next state and rendering updates
- Number of neurons and synapses that can be simulated without crashing

## Guide to recreate tests
1. Clone the following repositories and run locally:
    - [v2](https://github.com/lmgal/websnapse_extended-test)
    - [v3](https://github.com/lmgal/websnapse-v3) or [Reloaded](https://github.com/websnapse/websnapse.github.io)
2. Download systems on output folder 
3. Check the console on browser to check logs

## Guide to generate more systems
If higher neurons that what is already available in the repository is needed, main.py can be used
1. Install Python
2. Change constants on main.py
3. Run