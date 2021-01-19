# EnergySim

### Simulation of an energy market with multi-processing and multi-threading by RODHAIN David and LORRAIN Thomas

## Structure

- 2 files : 1 client (maison.py) and 1 server (market.py)
- 1 Message Queue between Home processes and the main process of market.py
- 1 Message Queue between Home processes
- Each Home is a process
- Market is multi-threaded : each thread manages a transaction
- Economics, Politics processes produces signals
- Weather process updates the temperature

The simulation is turn-based, it will show the evolution of the energy price for each turn. Home processes make one transaction per turn (Give, Sell, Buy) 

## How to launch the Sim

- Launch 2 terminals that include sysv_ipc module

- In the first one, launch market.py without arguments

- In the second one, launch maison.py with an argument : the number of houses you want (Integer expected)

- To end properly the simulation, make sure you're in the market terminal and press CTRL + C, it will end properly on the client side automatically

  