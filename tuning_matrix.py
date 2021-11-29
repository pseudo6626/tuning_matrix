# Helper script to adjust parameters based on Z level
#
# Copyright (C) 2019  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

# command TUNING_MATRIX ROWS=<> COLS=<> X_CMD=<> X_PARAM=<> X_MIN=<> X_MAX=<> DEL_X=<> Y_CMD=<> Y_PARAM=<>  Y_MIN=<> Y_MAX=<> DEL_Y=<> CMD=<> PARAM=<> MIN=<> MAX=<> DEL=<>
# needs header [tuning_matrix] in cfg with parameter: bed_dim=[xmin,xmax,ymin,ymax]
import math, logging, ast

CANCEL_Z_DELTA=2.0

class TuningMatrix:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.normal_transform = None
        try:
            self.dims=ast.literal_eval(config.get('bed_dim'))
            self.xrange=self.dims[1]-self.dims[0]
            self.yrange=self.dims[3]-self.dims[2]
        except:
            raise config.error("cannot locate or parse bed_dim. make sure is present and formatted correctly")
        self.last_position = [0., 0., 0., 0.]
        self.last_x = self.last_y = self.last_z =self.x_min = self.y_min = self.x_max =self.y_max = self.x_del = self.y_del = self.min=self.max=self.delta= 0.
        self.last_command_values = []
        self.command_fmt = self.command_fmt_x = self.command_fmt_y =  ""
        self.gcode_move = self.printer.load_object(config, "gcode_move")
        # Register command
        self.gcode = self.printer.lookup_object("gcode")
        self.gcode.register_command("TUNING_MATRIX", self.cmd_TUNING_MATRIX,
                                    desc=self.cmd_TUNING_MATRIX_help)
    cmd_TUNING_MATRIX_help = "Tool to adjust a parameter at different cells in a user defined xy grid"
    def cmd_TUNING_MATRIX(self, gcmd):
        if self.normal_transform is not None:
            self.end_test()
        # Get collums and rows, and determine x,y coordinates for all 4 sides of each cell
        self.rows=int(gcmd.get_float('ROWS',1))
        self.gcmd=gcmd
        self.cols=int(gcmd.get_float('COLS',1))
        self.cell_count=self.cols*self.rows
        self.cell_width=int(self.xrange/self.cols)
        self.cell_height=int(self.yrange/self.rows)
        self.cell_walls=[]
        self.cell_topbot=[]
        for i in range(self.dims[0],self.dims[1]+self.cell_width,self.cell_width):
            self.cell_walls.append(i)
        for j in range(self.dims[2],self.dims[3]+self.cell_height,self.cell_height):
            self.cell_topbot.append(j)
        #get commands, parameters, mins maxes and deltas
        message_parts = []
        message_parts.append("total_cells=%d" % (self.cell_count,))
        message_parts.append("cell_width=%.6f" % (self.cell_width,))
        message_parts.append("cell_height=%.6f" % (self.cell_height,))
        self.command = gcmd.get('CMD',None)
        self.x_cmd = gcmd.get('X_CMD',None)
        self.y_cmd =gcmd.get('Y_CMD',None)
        if self.command != None and self.x_cmd == None and self.y_cmd == None:  #if general CMD is used (parameter is changed linearly left-right bottom-top)
            parameter = gcmd.get('PARAM',None)
            self.min=gcmd.get_float('MIN',0.)
            self.max=gcmd.get_float('MAX',0.)
            self.delta=gcmd.get_float('DEL',0.)
            message_parts.append("start=%.6f" % (self.min,))
            if parameter == None:
                raise gcmd.error("PARAM must be defined if using CMD")
            if self.max != 0. and self.delta != 0.:
                raise gcmd.error("Cannot specify both MAX and DEL when using CMD, pick only one")
            if self.max !=0.0:
                self.delta=(self.max-self.min)/max(self.cell_count-1,1)
            message_parts.append("delta=%.6f" % (self.delta,))
            if self.gcode.is_traditional_gcode(self.command):
                self.command_fmt = "%s %s%%.9f" % (self.command, parameter)
            else:
                self.command_fmt = "%s %s=%%.9f" % (self.command, parameter)
        elif self.command == None and (self.x_cmd != None or self.y_cmd != None):  # if X_CMD and or Y_CMD are used (parameter for X_CMD changed linearly left-right, parameter for Y_CMD changed linearly bottom-top)
            x_param=gcmd.get('X_PARAM',None)
            self.x_min=gcmd.get_float('X_MIN',0.)
            self.x_max=gcmd.get_float('X_MAX',0.)
            self.x_del=gcmd.get_float('X_DEL',0.)
            message_parts.append("x_start=%.6f" % (self.x_min,))
            if x_param == None and self.x_cmd != None:
                raise gcmd.error("X_PARAM must be defined if using X_CMD")
            if self.x_max != 0. and self.x_del != 0.:
                raise gcmd.error("Cannot specify both X_MAX and X_DEL when using X_CMD, pick only one")
            if self.gcode.is_traditional_gcode(self.x_cmd):
                self.command_fmt_x = "%s %s%%.9f" % (self.x_cmd, x_param)
            else:
                self.command_fmt_x = "%s %s=%%.9f" % (self.x_cmd, x_param)
            if self.x_max:
                self.x_del=(self.x_max - self.x_min)/max(self.cols-1,1)
            message_parts.append("x_delta=%.6f" % (self.x_del,))
            y_param=gcmd.get('Y_PARAM',None)
            self.y_min=gcmd.get_float('Y_MIN',0.)
            self.y_max=gcmd.get_float('Y_MAX',0.)
            self.y_del=gcmd.get_float('Y_DEL',0.)
            message_parts.append("y_start=%.6f" % (self.y_min,))
            if y_param == None and self.y_cmd != None:
                raise gcmd.error("Y_PARAM must be defined if using Y_CMD")
            if self.y_max != 0. and self.y_del != 0.:
                raise gcmd.error("Cannot specify both Y_MAX and Y_DEL when using Y_CMD, pick only one")
            if self.gcode.is_traditional_gcode(self.y_cmd):
                self.command_fmt_y = "%s %s%%.9f" % (self.y_cmd, y_param)
            else:
                self.command_fmt_y = "%s %s=%%.9f" % (self.y_cmd, y_param)
            if self.y_max:
                self.y_del=(self.y_max - self.y_min)/max(self.rows-1,1)
            message_parts.append("y_delta=%.6f" % (self.y_del,))
        else:
             raise gcmd.error("Atleast one of CMD, X_CMD, or Y_CMD must be declaired")
        # Enable test mode
        nt = self.gcode_move.set_move_transform(self, force=True)
        self.normal_transform = nt
        self.last_x = self.last_y = self.last_z  = -99999999.9
        self.last_command_value = None
        self.get_position()
        gcmd.respond_info(
            "Starting tuning test (" + " ".join(message_parts) + ")")
    def get_position(self):
        pos = self.normal_transform.get_position()
        self.last_position = list(pos)
        return pos
    def locate(self,checks,val):
        for i in checks:
            if val <= i:
                return round((checks.index(i)+1.1)/2)
        return "e"
    def calc_value(self, pos):
        # check if in CMD or X,Y mode
        new_vals=[]
        x_count=self.locate(self.cell_walls,pos[0])
        logging.info("x_count: %d" % (x_count,))
        if x_count=="e":
            raise self.gcmd.error("Error: position not located within grid")
        y_count=self.locate(self.cell_topbot,pos[1])
        logging.info("y_count: %d" % (y_count,))
        if y_count=="e":
            raise self.gcmd.error("Error: position not located within grid")       
        if self.command:
            new_vals.append(self.min + self.delta*(self.cols*max(y_count-2,0)+max(x_count-1,0)))
        elif self.y_cmd:
            if self.x_cmd:
                new_vals.append(self.x_min + self.x_del*max(x_count-1,0))
            new_vals.append(self.y_min + self.y_del*max(y_count-1,0))
        return new_vals
    def move(self, newpos, speed):
        normal_transform = self.normal_transform
        z = newpos[2]
        if z < self.last_z - CANCEL_Z_DELTA:
            # Extrude at a lower z height - probably start of new print
            self.end_test()
        else:
            # Process update
            gcode_pos = self.gcode_move.get_status()['gcode_position']
            parsed_pos=[gcode_pos.x,gcode_pos.y,gcode_pos.z]
            newvals = self.calc_value(parsed_pos)
            if newvals != self.last_command_values:
                if len(newvals) == 1:
                    self.gcode.run_script_from_command(self.command_fmt % (newvals[0],))
                elif len(self.last_command_values)>1:
                    if self.last_command_values[0] != newvals[0]:
                        self.gcode.run_script_from_command(self.command_fmt_x % (newvals[0],))
                    if self.last_command_values[1] != newvals[1]:
                        self.gcode.run_script_from_command(self.command_fmt_y % (newvals[1],))
                else:
                    self.gcode.run_script_from_command(self.command_fmt_x % (newvals[0],))
                    self.gcode.run_script_from_command(self.command_fmt_y % (newvals[1],))
                self.last_command_values = newvals
        # Forward move to actual handler
        self.last_position[:] = newpos
        normal_transform.move(newpos, speed)
    def end_test(self):
        self.gcode.respond_info("Ending tuning test mode")
        self.gcode_move.set_move_transform(self.normal_transform, force=True)
        self.normal_transform = None

def load_config(config):
    return TuningMatrix(config)
