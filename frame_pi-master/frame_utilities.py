import pickle
import os
import random

def load_frame_variables():
    BASE_DIR =  "/home/pi/frame_pi"
    variables_path = os.path.join(BASE_DIR, 'frame_variables')

    if os.path.isfile(variables_path) == False:
        frame_name = "SwitchCraft_" + str(random.randint(1,10000))
        frame_variables = {'frame_name':frame_name}
        file = open(variables_path, 'wb')
        pickle.dump(frame_variables, file)
        file.close()
        return frame_variables
    else:
        file = open(variables_path, 'rb')
        frame_variables = pickle.load(file)
        file.close()
        return frame_variables


if __name__ == '__main__':
    r = load_frame_variables()
    print(r)