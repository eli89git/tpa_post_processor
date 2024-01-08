import PySimpleGUI as sg

tools_diameter = [8.0,12.0,5.0,5.0,5.0,25.0,35.0,4.0,15.0]

#--------------------------------Function to convert TCN file-------------------------------#
def convert_tcn_file(file_path):
    try:
        # Initialize variables to store different sections of the TCN file
        converted_file = []
        in_drilling_section = False
        drilling_command_ready = False
                
        previous_tool_number = None
        #tool_number = None
        previous_x = None
        previous_y = None
        min_z = None
        
        # Open the selected TCN file for reading
        with open(file_path, 'r') as tcn_file:
            tcn_content = tcn_file.readlines()

        # Process each line in the TCN file
        for line in tcn_content:         

            if line.startswith("W#89{"):
                # Check if this line indicates the start of a section
                if "#205=" in line:
                    between_braces = line.split("{", 1)[1].split("}")[0]
                    if "#205=" in between_braces:
                        tool_number = between_braces.split("#205=")[1].split()[0]
                        if tool_number.isdigit() and 1 <= int(tool_number) <= 9:
                            in_drilling_section = True
                        else:
                            if in_drilling_section:
                                update_drilling_command(previous_x, previous_y, min_z, previous_tool_number, converted_file)
                                in_drilling_section = False
                            update_none_drilling_command(line, converted_file)
                else:
                    return f"Error: Section without tool"
            
                
            # Check if this line contains drilling information
            elif line.startswith("W#2201{"):
                if in_drilling_section:
                    # Extract drilling coordinates and depth from the line
                    parts = line.split()
                    x_coord = parts[2].split('=')[1]
                    y_coord = parts[3].split('=')[1]
                    depth = parts[4].split('=')[1]

                    # Convert coordinates and depth to float
                    x_coord = float(x_coord)
                    y_coord = float(y_coord)
                    depth = float(depth)

                    # If coordinates have not changed, update the minimum depth
                    if x_coord == previous_x and y_coord == previous_y:
                        if min_z is None or depth < min_z:
                            min_z = depth
                    else:
                        # Create the corresponding W#81 command for the previous point
                        if previous_x is not None and previous_y is not None and min_z is not None and previous_tool_number is not None:
                            update_drilling_command(previous_x, previous_y, min_z, previous_tool_number, converted_file)                            
                        
                        # Update the previous coordinates and minimum depth    
                        previous_tool_number = tool_number  
                        previous_x = x_coord
                        previous_y = y_coord
                        min_z = depth
                else:
                    update_none_drilling_command(line, converted_file)

            elif not line.startswith("#1001") and  not line.startswith("#8181"):
                if in_drilling_section:
                    update_drilling_command(previous_x, previous_y, min_z, previous_tool_number, converted_file)   
                    in_drilling_section = False
                update_none_drilling_command(line, converted_file)
                previous_tool_number = None
                tool_number = None         

        converted_file_path = save_converted_file(file_path, converted_file)

        return f"Conversion completed. Saved as {converted_file_path}"

    except Exception as e:
        return f"Error: {str(e)}"

#--------------------------------------------------------------------------------------#
def update_drilling_command (x_coord, y_coord, min_z, tool_number, converted_file):
    drilling_command = f"W#81{{ ::WTp WS=1 #8015=0 #1={x_coord} #2={y_coord} #3={min_z} #1002={tools_diameter[int(tool_number)-1]} #201=1 #203=1 #204=0 #205={tool_number} #1001=1 }}W\n"
    converted_file.append(drilling_command)
#--------------------------------------------------------------------------------------#

#--------------------------------------------------------------------------------------#
def update_none_drilling_command(line, converted_file):
    converted_file.append(line)
#--------------------------------------------------------------------------------------#
    
#--------------------------------------------------------------------------------------#
def save_converted_file(file_path, converted_file):
    # Combine the sections in the correct order to create the new TCN content
    new_tcn_content = "".join(converted_file)

    # Create a new TCN file with the converted content
    converted_file_path = file_path.replace(".tcn", "_converted.tcn")
    with open(converted_file_path, 'w') as converted_file:
        converted_file.write(new_tcn_content)
    return converted_file_path
#--------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------#
# Define the PySimpleGUI layout
layout = [
    [sg.Text("Select a TCN file to convert:")],
    [sg.InputText(key="file_path", disabled=True), sg.FileBrowse()],
    [sg.Button("Convert"), sg.Exit()],
    [sg.Text("", key="result", size=(40, 3))]
]

# Create the PySimpleGUI window
window = sg.Window("TCN File Converter", layout)

# Event loop
while True:
    event, values = window.read()

    if event == sg.WINDOW_CLOSED or event == "Exit":
        break
    elif event == "Convert":
        file_path = values["file_path"]
        if file_path:
            result = convert_tcn_file(file_path)
            window["result"].update(result)

# Close the window
window.close()
