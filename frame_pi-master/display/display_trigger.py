import os
import pickle


class DisplayTrigger():

    def __init__(self):
        # self.BASE_DIR = os.getcwd()
        self.BASE_DIR =  "/home/pi/frame_pi"
        self.DISPLAY_DIR = os.path.join(self.BASE_DIR, 'display')
        self.display_manager = os.path.join(self.DISPLAY_DIR,'test_manager.py')
        self.variables_file = os.path.join(self.DISPLAY_DIR, 'variables')
    
    def trigger_display(self, display_url=None, orientation=None, wifi_connected=None):
        # load variables
        file = open(self.variables_file, 'rb')
        variables = pickle.load(file)
        file.close()

        if display_url is not None:
            variables['display_url'] = display_url
        if orientation is not None:
            variables['orientation'] = orientation
        if wifi_connected is not None:
            variables['wifi_connected'] = wifi_connected
        
        file = open(self.variables_file, 'wb')
        pickle.dump(variables, file)
        file.close()

        if display_url is not None: 
            msg = 'successfully loaded new url to frame'
        else:
            msg = None

        response = {
            'success':True,
            'type':'load_url_frame',
            'msg':msg
        }
        return response