# tuning_matrix

tuning_matrix is a new way to tune parameters in Klipper. Instead of adjusting parameters by layer height a la tuning_tower, tuning_matrix instead adjusts parameter values based on x and y coordinates. 

Depending on the inputs for ROWS and COLS, tuning_matrix divides your printers bed into a series of cells. For any actions done within each cell, tuning_matrix changes the user defined parameters accordingly. 

This not only allows for shorter (and thus faster) calibration prints, but also for the option to tune two different parameters codependently. (one tuned along the x, the other along the y)

to use tuning_matrix, first, add the following to your printer.cfg file:

[tuning_matrix]
bed_dim=[xmin,xmax,ymin,ymax] #Where xmin,xmax,ymin,ymax are the min max coordinates of your bed in mm

Next, copy the tuning_matrix.py file in this depot into your pi/home/klipper/klippy/extras  folder on your klipper controling raspberry pi. And that is it!

The command structure of tuning_matrix is as follows:

two mode of use:

CMD - only one command to be changed for both x and y. The value will be changed left to right, bottom to top in a zig zag pattern. Value starts at MIN and will be changed each cell either by the user provided DEL value, or if the user provides MAX, will calculate the appropriate incriment based on total number of cells

TUNING_MATRIX ROWS=[number of rows] COLS=[number of collumns]  CMD=[command to be changed] PARAM=[parameter to be changed for command] MIN=[min value for parameter] MAX=[max value for parameter] DEL=[ammount to change parameter for each cell]

  
  
X_CMD and Y_CMD - two different commands will be used for both x and y. in this case, parameters, min, and max or del values must be given for each x and y.

TUNING_MATRIX ROWS=[number of rows] COLS=[number of collumns]  X_CMD=[klipper command for x direction] X_PARAM=[parameter to be changed for x command] X_MIN=[min value for x param] X_MAX=[max value for x param] DEL_X=[ammount to change x param for each cell] Y_CMD=[klipper command for y direction] Y_PARAM=[parameter to be changed for y command] Y_MIN=[min value for y param] Y_MAX=[max value for y param] DEL_Y=[ammount to change y param for each cell]

