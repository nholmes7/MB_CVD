from MFC_functions import MFC_command
import threading, time

def run_recipe():
    MFC_1 = 101
    MFC_2 = 102
    MFC_3 = 103

    recipe = []

    with open('example_recipe','r') as file:
        for line in file:
            if line[0] != '#':
                print(line)
                recipe.append(line[:-1].split(','))

    recipe = [[float(j) for j in i] for i in recipe]
    time_points = [i[0] for i in recipe]
    temp_points = [i[1] for i in recipe]
    gas_1_points = [i[2] for i in recipe]
    gas_2_points = [i[3] for i in recipe]
    gas_3_points = [i[4] for i in recipe]

    # loop through the recipe instructions
    start_time = time.time()
    i = 0
    for time_step in time_points:
        # use threading for setting the flows so the program doesn't hang
        MFC1_task = threading.Thread(target=MFC_command,args=(MFC_1,'set_flow',gas_1_points[i]))
        MFC2_task = threading.Thread(target=MFC_command,args=(MFC_2,'set_flow',gas_2_points[i]))
        MFC3_task = threading.Thread(target=MFC_command,args=(MFC_3,'set_flow',gas_3_points[i]))

        MFC1_task.start()
        MFC2_task.start()
        MFC3_task.start()

        # some print statements for debugging
        print('Setting temperature to ' + str(temp_points[i]))
        print('Setting gas 1 to ' + str(gas_1_points[i]))
        print('Setting gas 2 to ' + str(gas_2_points[i]))
        print('Setting gas 3 to ' + str(gas_3_points[i]))
        print(str(time.time()-start_time))

        time.sleep(time_step)

        i = i + 1