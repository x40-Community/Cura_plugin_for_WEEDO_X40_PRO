# Copyright (c) 2022, 2023 X40-Community
# Cura is released under the terms of the LGPLv3 or higher.
# Weedo X40 PRO Plugin Rev. 2.0.0 for Ultimaker Cura 5.X
# 
#Last changes:
# The operating concept has been revised to avoid errors

import math
import platform
from UM.Application import Application
from UM.Logger import Logger
from cura.Snapshot import Snapshot
from PyQt6.QtCore import QByteArray, QIODevice, QBuffer

from ..Script import Script


class Weedo_X40_PRO(Script):
    def __init__(self):
        super().__init__()


    def _createSnapshot(self, width, height):
        Logger.log("d", "Creating thumbnail image...")
        try:
            return Snapshot.snapshot(width, height)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")

    def _convertSnapshotToGcode(self, snapshot):
        Logger.log("d", "Encoding thumbnail image...")
        try:
            # create a "virtual file" as buffer to store our thumbnail as jpeg
            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            
            # save our snapshot as the virtual jpeg file
            thumbnail_image = snapshot
            thumbnail_image.save(thumbnail_buffer, "JPG")

            # rewind our buffer, so that we read the whole jpeg
            thumbnail_buffer.seek(0)
            
            # generate our gcode by reading one byte at a time
            # the display expects the begin of a screenhot as "W221", 
            # every other line as "W220" and the "W222" as End-Of-File.
            # The read bytes are converted to hex numbers.
            # The hey numbers are appended to the current line until it reached 40 bytes.
            # Once 40 bytes is reached, the line is added to the g-code and a new line is started.
            # Finally, once all byted have been read, the End-Of-File is declared using "W222"
            gcode = []
            newline = "W221"
            byte = thumbnail_buffer.read(1)
            counter = 0
            while byte != b"":
                if counter == 0:
                    gcode.append(newline)
                    newline = "W220 "
                    counter = 40
                newline += byte.hex()
                counter -= 1

                byte = thumbnail_buffer.read(1)
            gcode.append(newline)
            gcode.append("W222")

            # The "virtual file" is being closed and therefore deleted.
            thumbnail_buffer.close()
            return gcode
        except Exception:
            Logger.logException("w", "Failed to encode snapshot image")

    def getSettingDataString(self):
        return """{
            "name": "Weedo X40 PRO Plugin",
            "key": "Weedo_X40_PRO",
            "metadata": {},
            "version": 2,
            "settings":
            {
                 "disable_abl":
                {
                    "label": "Use EEPROM data for mesh",
                    "description": "This feature disables automatic bed leveling at startup and instead uses the latest EEPROM data for the mesh.",
                    "type": "bool",
                    "default_value": false
                },
                 "insert_thumbnail":
                {
                    "label": "Insert Thumbnail",
                    "description": "Activate this feature to insert JPEG thumbnail for Printer Display.",
                    "type": "bool",
                    "default_value": true
                },
                 "power_off":
                {
                    "label": "Switch Power off after printing",
                    "description": "Activate this feature to turn off the printer after printing (M81 Command).",
                    "type": "bool",
                    "default_value": false
                },
                 "power_loss":
                {
                    "label": "Disable Power-loss Recovery",
                    "description": "Activate this feature to disable the power-loss recovery function (M413 Command). Switching off can be particularly useful when printing via USB or network.",
                    "type": "bool",
                    "default_value": false
                },
                 "runout_sensor":
                {
                    "label": "Disable Runout Sensor",
                    "description": "Activate this feature to turn off the runout sensor (M412 Command). Switching off can be particularly useful when printing via USB or network.",
                    "type": "bool",
                    "default_value": false
                },
                "multiple_wipes":
                {
                    "label": "Disable  Multiwipes",
                    "description": "Activate this feature to disable the multiple wipes function befor tool change (M923 Command). Use this function, when you want use a prime tower.",
                    "type": "bool",
                    "default_value": false
                },
                "purge_extrusion":
                {
                    "label": "Disable Auto purge",
                    "description": "Activate this feature to disable the automatic purge extrusion befor tool change (M922 Command). Use this function, when you want use a prime tower.",
                    "type": "bool",
                    "default_value": false
                },
                
                "purge_mode": {
                    "label": "Purge mode",
                    "description": "Parking position: Parking position is suitable for all print modes.                    Purge line: Purge line cannot be used in dual print mode.                      Duplicate / Mirror: As the name suggests, Duplicate / Mirror mode can only be used in Duplicate / Mirror print mode",
                    "type": "enum",
                    "options": {"parking_purge": "Parking position", "print_purgeline": "Purge line", "duplicate_purge": "Duplicate / Mirror"},
                    "default_value": "parking_purge",
                    "enabled": "not purge_extrusion"
                },
                
                 "insert_pause":
                {
                    "label": "Insert pause at layer",
                    "description": "Activate this function to insert pause command after layernumber (M0 Command). The Weedo X40 PRO Printer only pauses when printing from the MicroSD card. Continue printing via display.",
                    "type": "bool",
                    "default_value": false
                },          
                "layer_number":
                {
                    "label": "Pause after layernumber",
                    "description": "Printer pause after layernumber",
                    "unit": "",
                    "type": "str",
                    "default_value": "10",
                    "minimum_value": "1",
                    "enabled": "insert_pause"
                },
                "slow_cooldown": 
                {
                    "label": "Cool down build plate slowly",
                    "description": "Activate this function to slowly cool down the buildplate. The function reduces residual stresses in materials with hugh shrinkage such as ABS. Disable Auto Power Off and Power Save Mode for use on the printer touch display",
                    "type": "bool",
                    "default_value": false
                },
                "end_temperature":
                {
                    "label": "End temperature",
                    "description": "The last temperature that is being held for a while.",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 30,
                    "minimum_value": "25",
                    "minimum_value_warning": "28",
                    "maximum_value_warning": "40",
                    "enabled": "slow_cooldown"
                },
                "cooling_time":
                {
                    "label": "Cool down time",
                    "description": "Duration of the cooling process.",
                    "unit": "min",
                    "type": "int",
                    "default_value": 60,
                    "minimum_value": "40",
                    "minimum_value_warning": "45",
                    "maximum_value_warning": "180",
                    "enabled": "slow_cooldown"
                }
                
            }
        }"""


    def execute(self, data):
        disable_abl = self.getSettingValueByKey("disable_abl")
        insert_thumbnail = self.getSettingValueByKey("insert_thumbnail")
        power_off = self.getSettingValueByKey("power_off")
        power_loss = self.getSettingValueByKey("power_loss")
        runout_sensor = self.getSettingValueByKey("runout_sensor")
        multiple_wipes = self.getSettingValueByKey("multiple_wipes")  
        purge_extrusion = self.getSettingValueByKey("purge_extrusion") 
        insert_pause = self.getSettingValueByKey("insert_pause")
        layer_nums = self.getSettingValueByKey("layer_number")
        slow_cooldown = self.getSettingValueByKey("slow_cooldown")
        start_temp = Application.getInstance().getGlobalContainerStack().getProperty("material_bed_temperature", "value")
        end_temp = self.getSettingValueByKey("end_temperature")
        cooling_time = self.getSettingValueByKey("cooling_time")
        
        width = 180
        height = 180

        snapshot = self._createSnapshot(width, height)
        if insert_thumbnail:
            snapshot_gcode = self._convertSnapshotToGcode(snapshot)

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                    if line.startswith(";Generated with Cura"):
                        line_index = lines.index(line)
                        insert_index = line_index + 1
                        lines[insert_index:insert_index] = snapshot_gcode
                        break

                final_lines = "\n".join(lines)
                data[layer_index] = final_lines

        if disable_abl:  
            insert_M420_command = "G1 Z10 F6000 ;Replaced by Weedo X40 PRO Plugin\nM420 S1 ;Replaced by Weedo X40 PRO Plugin"
            for layer in data:
                layer_index = data.index(layer)
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith("G29"):
                        line_index = lines.index(line)
                        lines[line_index] = insert_M420_command
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines

        if insert_pause:
            insert_M0_command = "M0 ;Print pause generated by Weedo X40 PRO Plugin\n"

            layer_targets = layer_nums.split(",")
            if len(layer_targets) > 0:
                for layer_num in layer_targets:
                    try:
                        layer_num = int(layer_num.strip()) + 1 
                    except ValueError: 
                        continue
                    if 0 < layer_num < len(data):
                        data[layer_num] = insert_M0_command + data[layer_num]

        if slow_cooldown: 
            steps = int(start_temp - end_temp)
            milliseconds_per_step = int(cooling_time * 60000 / steps)
            code = "\n"
            current_temp = int(start_temp - 1)
            insert_cooldown_command = "M140 S{current_temp}\nG4 P{milliseconds_per_step}\n"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";End of Gcode"):
                      for i in range(steps):
                          lines.insert(layer_index, f"M140 S{current_temp} ;Slow cooldown buildplate generated by Weedo X40 PRO Plugin\nG4 P{milliseconds_per_step}")
                          current_temp -= 1
                      lines.insert(layer_index, "M140 S0 ;Stop buildplate heating generated by Weedo X40 PRO Plugin\n")
                      break

                result = "\n".join(lines)
                data[layer_index] = result

     
        if power_off:
            insert_M81_command = "M81 ;Printer Power off generated by Weedo X40 PRO Plugin\n"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";End of Gcode"):
                      lines.insert(layer_index, insert_M81_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result

        if power_loss:
            insert_M413_command = "M413 S0 ;Disable Power-loss recovery generated by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M413_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result
        else:
            insert_M413_command = "M413 S1 ;Enable Power-loss recovery generated by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M413_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result

        if runout_sensor:
            insert_M412_command = "M412 S0 ;Disable filament runout detection generated by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M412_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result
        else:
            insert_M412_command = "M412 S1 ;Enable filament runout detection generated by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M412_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result


        if multiple_wipes:
            insert_M923_command = "M923 S0 ;Disable multiwipe function by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M923_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result
        else:
            insert_M923_command = "M923 S1 ;Enable multiwipe function by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M923_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result


        if purge_extrusion:
            insert_M922_command = "M922 S0 ;Disable pre-extrusion function by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M922_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result
        else:
            insert_M922_command = "M922 S1 ;Enable pre-extrusion function by Weedo X40 PRO Plugin"

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                   if line.startswith(";Generated with Cura"):
                      lines.insert(layer_index, insert_M922_command)
                      break

                result = "\n".join(lines)
                data[layer_index] = result



        if self.getSettingValueByKey("purge_mode") == "print_purgeline" and not purge_extrusion:
            for layer_number, layer in enumerate(data):
                  data[layer_number] = layer.replace("G1 E50 F100 ; Extrude in parking position", "G1 Z5.0 F3000 ;Move Z Axis up replaced by Weedo X40 PRO Plugin\nG1 X0 Y20 Z0.28 F5000.0 ;Move to start position replaced by Weedo X40 PRO Plugin\nG1 X0 Y200.0 Z0.28 F1500.0 E15 ;Print the first purge line replaced by Weedo X40 PRO Plugin\nG1 X0 Y200.0 Z0.28 F5000.0 ;Move to side a little replaced by Weedo X40 PRO Plugin\nG1 X0 Y20 Z0.28 F1500.0 E30 ;Print the second purge line replaced by Weedo X40 PRO Plugin\nG1 Z2.0 F3000 ;Move Z Axis up replaced by Weedo X40 PRO Plugin")            

        if self.getSettingValueByKey("purge_mode") == "duplicate_purge" and not purge_extrusion:
            for layer_number, layer in enumerate(data):
                  data[layer_number] = layer.replace("G1 E50 F100 ; Extrude in parking position", "G1 Y300 F5000 ;Move to duplicate/mirrored mode purge position replaced by Weedo X40 PRO Plugin\nG1 E50 F100 ;Extrude in duplicate/mirrored mode purge position replaced by Weedo X40 PRO Plugin") 
            






        if platform.system() == 'Linux' or platform.system() == 'Darwin':     
            for layer in data:
                layer_index = data.index(layer)
                # convert Windows lineendings (\r\n) and Mac lineendings (\r) to Linux lineendings (\n)
                # split each line based on the lineending
                lines = data[layer_index].replace("\r\n", "\n").replace("\r", "\n").split("\n")
                
                # convert all lines to use the Windows linenedings
                # the X40 Display has a bug where it can only parse those...
                final_lines = "\r\n".join(lines)
                
                # replace the old layer data with the new layer data
                # including the snapshot and fixed line endings
                data[layer_index] = final_lines

        return data
