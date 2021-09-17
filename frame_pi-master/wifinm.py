import NetworkManager
from blufi import AbstractWiFiHandler
from uptime import uptime, boottime
from blufi.tools import report_exception
import uuid

class WiFiHandlerNetworkManager(AbstractWiFiHandler):
    def __init__(self):
        AbstractWiFiHandler.__init__(self)
        self.c = NetworkManager.const

    @report_exception
    def InitiateScan(self):
        #this function must be asynchronous (nonblocking)
        print('inititate Wifi SCAN in the background')
        try:
            for dev in NetworkManager.NetworkManager.GetDevices():
                if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
                    continue

                if uptime() - dev.LastScan/1000.0 < 30: 
                    #avoid Exception too many scan requests
                    continue

                try:
                    dev.RequestScan(options=dict())
                except Exception as e:
                    print('Scan failed', e)
                    pass
        except Exception as e:
            print('InitiateScan failed', e)

    @report_exception
    def CheckScanResult(self):
        """Check whether WiFi scan finished and return the result"""
        #this function is called 10x per second
        self.scantries += 1
        if self.scantries >= 50: 
            self.scantries = 0
            print('Wifi SCAN completed')

            resp = []

            try:

                for dev in NetworkManager.NetworkManager.GetDevices():
                    if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
                        continue
                    
                    active = dev.ActiveAccessPoint
                    aps = dev.GetAllAccessPoints()
                    for ap in sorted(aps, key=lambda obj:obj.Strength, reverse=True):
                        prefix = '* ' if (active is not None) and (ap.object_path == active.object_path) else '  '
                        print("%s %s  %s lastseen:%d, mode:%d, rssi:%d, wpaf:%d" % (prefix, ap.Ssid, ap.HwAddress, ap.LastSeen, ap.Mode, ap.Strength, ap.WpaFlags))  
                        #SIGNAL value is a percentage. Maximum signal value is 100.
                        #A value of 0 implies an actual RSSI signal strength of -100 dbm. A value of 100 implies an actual RSSI signal strength of -50 dbm.
                    
                        if(ap.Strength <= 0):
                            dBm = -100
                        elif(ap.Strength >= 100):
                            dBm = -50
                        else:
                            dBm = (ap.Strength / 2) - 100

                        resp.append({'SSID': ap.Ssid.encode('utf-8'), 'RSSI': int(dBm)})

            except Exception as e:
                print('GetAllAccessPoints failed', e)

            #print('response:', resp)
            return resp
           
        #no result available yet
        return None


    @report_exception
    def GetWifiStatus(self):
        print('WIFI STATUS requested')
        activeSSID, isConnected = None, False

        for conn in NetworkManager.NetworkManager.ActiveConnections:
            settings = conn.Connection.GetSettings()

            for dev in conn.Devices:
                if not self.c('device_type', dev.DeviceType) == 'wifi':
                    continue

                if '802-11-wireless' in settings:
                    ssid = settings['802-11-wireless']['ssid'] if 'ssid' in settings['802-11-wireless'] else None
                    #print(ssid)
                    #print("Device: %s" % dev.Interface)
                    #print("   Type             %s" % self.c('device_type', dev.DeviceType))
                    activeSSID, isConnected = ssid.encode('utf-8'), dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED

#static const char *state_table[] = {
#	[NM_DEVICE_STATE_UNKNOWN]      = QUEUED_PREFIX "unknown",
#	[NM_DEVICE_STATE_UNMANAGED]    = QUEUED_PREFIX "unmanaged",
#	[NM_DEVICE_STATE_UNAVAILABLE]  = QUEUED_PREFIX "unavailable",
#	[NM_DEVICE_STATE_DISCONNECTED] = QUEUED_PREFIX "disconnected",
#	[NM_DEVICE_STATE_PREPARE]      = QUEUED_PREFIX "prepare",
#	[NM_DEVICE_STATE_CONFIG]       = QUEUED_PREFIX "config",
#	[NM_DEVICE_STATE_NEED_AUTH]    = QUEUED_PREFIX "need-auth",
#	[NM_DEVICE_STATE_IP_CONFIG]    = QUEUED_PREFIX "ip-config",
#	[NM_DEVICE_STATE_IP_CHECK]     = QUEUED_PREFIX "ip-check",
#	[NM_DEVICE_STATE_SECONDARIES]  = QUEUED_PREFIX "secondaries",
#	[NM_DEVICE_STATE_ACTIVATED]    = QUEUED_PREFIX "activated",
#	[NM_DEVICE_STATE_DEACTIVATING] = QUEUED_PREFIX "deactivating",
#	[NM_DEVICE_STATE_FAILED]       = QUEUED_PREFIX "failed",
#};

        return activeSSID, isConnected

    @report_exception
    def Connect(self):
        #connect requested
        print('CONNECT to AP', self.config)

        #remove all configurations
        for conn in NetworkManager.Settings.ListConnections():
            conn.Delete()


        #add new configuration
        connuid = str(uuid.uuid4())
        connection = {
             '802-11-wireless': {'mode': 'infrastructure',
                                'security': '802-11-wireless-security',
                                'ssid': self.config['SSID'].decode('utf-8')},
             '802-11-wireless-security': {'auth-alg': 'open', 
                                          #'key-mgmt': 'wpa-eap'
                                         },
#             '802-1x': {'eap': ['peap'],
#                        'identity': 'eap-identity-goes-here',
#                        'password': 'eap-password-goes-here',
#                        'phase2-auth': 'mschapv2'},
            'connection': {'id': 'my-wifi-connection',
                           'type': '802-11-wireless',
                           'uuid': connuid},
            'ipv4': {'method': 'auto'},
            'ipv6': {'method': 'auto'}
        }

        if len(self.config['Passphrase']):
            connection['802-11-wireless-security']['key-mgmt'] = 'wpa-psk'
            connection['802-11-wireless-security']['psk'] = self.config['Passphrase'].decode('utf-8')

        try:
            NetworkManager.Settings.AddConnection(connection)
        except Exception as e:
            print("Can't add network connection", e)
            return False

        try:
            for conn in NetworkManager.Settings.ListConnections():
                settings = conn.GetSettings()
                if (not 'connection' in settings) or (not 'uuid' in settings['connection']) or (settings['connection']['uuid'] != connuid): 
                    continue
                
                devices = NetworkManager.NetworkManager.GetDevices()
                for dev in devices:
                    if not self.c('device_type', dev.DeviceType) == 'wifi':
                        continue
                        
                    #print('device', dev, conn)
                    print('Activating connection')
                    NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")
                    return True
        except Exception as e:
            print("Can't connect", e)

        return False


if __name__ == '__main__':
    import os, time

    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

    dev = WiFiHandlerNetworkManager()

    status = dev.GetWifiStatus()
    print(status)

    dev.config = {'SSID': b'MySSID', 'Passphrase': b'ABCDEFGHIJK'}
    dev.Connect()

    dev.InitiateScan()
    while True:
        wl = dev.CheckScanResult()
        if wl != None: 
            print(wl)
            break
        time.sleep(.1)    
