# FoosballTable

The automation code for a foosball table. 

The code is divided into 
  1. an arduino portion which is installed in the table hardware, and 
  2. a webserver that receives the table scoring and handles the UI for the game and general league statistics for a table


---
The latest arduino release uses a PIR sensor for goal scoring. This proven to be a bit unreliable at times.

The previous release is much more reliable with laser beams shining on a light sensor (the goal is scored when the laser light is "tripped").
Unfortunatelly, when a table is bumped a lot, this setting is fragile as the sensors will eventually misalign. 


