from bluezero import peripheral
from bluezero import async_tools
from .tools import report_exception

from bisturi.packet import Packet
from bisturi.field  import Bits, Int, Data

import abc

class FrameType(Packet):
    subtype = Bits(6) #MSB
    type = Bits(2) #LSB
    
    def __repr__(self):
        return f"{self.subtype:#08b} {self.type:#04b}"


class FrameControl(Packet):
    _          = Bits(3)
    isfrag     = Bits(1)
    reqack     = Bits(1)
    datadir    = Bits(1)
    hascheckum = Bits(1)
    encrypted  = Bits(1)
    
    def __repr__(self):
        return f"reqack:{self.reqack} dir:{self.datadir} ecnrypted:{self.encrypted} hascrc:{self.hascheckum} isfrag:{self.isfrag}"

class BluFiPacket(Packet):
    type     = FrameType
    fc       = FrameControl
    seq      = Int(byte_count=1, signed=False)
    length   = Int(byte_count=1, signed=False)
    data     = Data(byte_count=length, default=b'')
    checksum = Int(byte_count=2, signed=False).when(lambda pkt,**k: pkt.fc.hascheckum)
    
    def __repr__(self):
        return f"BluFiPacket type:{self.type} fc:{self.fc} seq:{self.seq} length:{self.length} data:\"{self.data}\""


class ApRecord(Packet):
      length  = Int(byte_count=1, signed=False)
      rssi    = Int(byte_count=1, signed=True)
      ssid    = Data(byte_count=length-1, default=b'')


BTC_BLUFI_GREAT_VER                          =  1  #Version + Subversion
BTC_BLUFI_SUB_VER                            =  2  #Version + Subversion

BLUFI_FC_DIR_P2E                             =  0
BLUFI_FC_DIR_E2P                             =  1

BLUFI_TYPE_CTRL                              =  0x00
BLUFI_TYPE_CTRL_SUBTYPE_ACK                  =  0x00
BLUFI_TYPE_CTRL_SUBTYPE_SET_SEC_MODE         =  0x01
BLUFI_TYPE_CTRL_SUBTYPE_SET_WIFI_OPMODE      =  0x02
BLUFI_TYPE_CTRL_SUBTYPE_CONN_TO_AP           =  0x03
BLUFI_TYPE_CTRL_SUBTYPE_DISCONN_FROM_AP      =  0x04
BLUFI_TYPE_CTRL_SUBTYPE_GET_WIFI_STATUS      =  0x05
BLUFI_TYPE_CTRL_SUBTYPE_DEAUTHENTICATE_STA   =  0x06
BLUFI_TYPE_CTRL_SUBTYPE_GET_VERSION          =  0x07
BLUFI_TYPE_CTRL_SUBTYPE_DISCONNECT_BLE       =  0x08
BLUFI_TYPE_CTRL_SUBTYPE_GET_WIFI_LIST        =  0x09

BLUFI_TYPE_DATA                              =  0x01
BLUFI_TYPE_DATA_SUBTYPE_NEG                  =  0x00
BLUFI_TYPE_DATA_SUBTYPE_STA_BSSID            =  0x01
BLUFI_TYPE_DATA_SUBTYPE_STA_SSID             =  0x02
BLUFI_TYPE_DATA_SUBTYPE_STA_PASSWD           =  0x03
BLUFI_TYPE_DATA_SUBTYPE_SOFTAP_SSID          =  0x04
BLUFI_TYPE_DATA_SUBTYPE_SOFTAP_PASSWD        =  0x05
BLUFI_TYPE_DATA_SUBTYPE_SOFTAP_MAX_CONN_NUM  =  0x06
BLUFI_TYPE_DATA_SUBTYPE_SOFTAP_AUTH_MODE     =  0x07
BLUFI_TYPE_DATA_SUBTYPE_SOFTAP_CHANNEL       =  0x08
BLUFI_TYPE_DATA_SUBTYPE_USERNAME             =  0x09
BLUFI_TYPE_DATA_SUBTYPE_CA                   =  0x0a
BLUFI_TYPE_DATA_SUBTYPE_CLIENT_CERT          =  0x0b
BLUFI_TYPE_DATA_SUBTYPE_SERVER_CERT          =  0x0c
BLUFI_TYPE_DATA_SUBTYPE_CLIENT_PRIV_KEY      =  0x0d
BLUFI_TYPE_DATA_SUBTYPE_SERVER_PRIV_KEY      =  0x0e
BLUFI_TYPE_DATA_SUBTYPE_WIFI_REP             =  0x0f
BLUFI_TYPE_DATA_SUBTYPE_REPLY_VERSION        =  0x10
BLUFI_TYPE_DATA_SUBTYPE_WIFI_LIST            =  0x11
BLUFI_TYPE_DATA_SUBTYPE_ERROR_INFO           =  0x12
BLUFI_TYPE_DATA_SUBTYPE_CUSTOM_DATA          =  0x13 

class AbstractWiFiHandler(abc.ABC):
    def __init__(self):
        self.scantries = 0
        self.config = {'SSID':None, 'Passphrase': None}

    @abc.abstractmethod
    def InitiateScan(self):
        #this function must be asynchronous (nonblocking)
        pass

    @abc.abstractmethod
    def CheckScanResult(self):
        pass

    @abc.abstractmethod
    def Connect(self):    
        pass


    @abc.abstractmethod
    def GetWifiStatus(self):    
        pass


class DeviceState():
    def __init__(self, dev):
        self.device = dev
        self.sendseq = 0
        self.frag_size = 128 #divna funkce, ATT umi pakety samo fragmentovat
        self.wifistate_tries_remain = 0

    def __repr__(self):
        return f'<DeviceState device: {self.device.address if self.device else "n/a"} connected: {self.device.connected if self.device else False} sendseq: {self.sendseq}'

DEBUG = False


class BluFi(peripheral.Peripheral):
    def __init__(self, wifi_handler_class, adapter_address, local_name, on_customdata=None):
        print('BLE address:', adapter_address)

        peripheral.Peripheral.__init__(self, adapter_address, local_name=local_name, appearance=1344)

        # Add service
        self.add_service(srv_id=1, uuid='FFFF', primary=True)

        # Add characteristic
        self.add_characteristic(srv_id=1, chr_id=1, uuid='FF02',
                                        value=[], notifying=False,
                                        flags=['read', 'notify'],
                                        read_callback=self.read_value,
                                        write_callback=None,
                                        notify_callback=self.notify
                                        )

         # Add characteristic
        self.add_characteristic(srv_id=1, chr_id=2, uuid='FF01',
                                        value=[], notifying=False,
                                        flags=['write'],
                                        read_callback=None,
                                        write_callback=self.write_value,
                                        )

        self.characteristic = None
        self.devices = {}
        self.sendseq = 0
        self.on_connect = self.on_connect_cb
        self.on_disconnect = self.on_disconnect_cb
        self.on_customdata = on_customdata
        self.wifi = wifi_handler_class()

    def on_disconnect_cb(self, dev):
        print('device disconnected')
        if dev.remote_device_path in self.devices:
            del self.devices[dev.remote_device_path]

    def on_connect_cb(self, dev):
        print('connected a device', dev)
        self.devices[dev.remote_device_path] = DeviceState(dev)
        
    @report_exception
    def read_value(self):
        if DEBUG: print('read')
        return []

    @report_exception
    def write_value(self, value, options):
        assert 'device' in options
        #if 'mtu' in options:
            #"mtu": Exchanged MTU (Server only)

        if DEBUG: 
            print('write',value,options, self.devices[options['device']])
            #print(self.device.name)#, self.device.RSSI)
        
        tlv = BluFiPacket.unpack(bytes(value))
        if tlv.fc.reqack:
            self.blufi_send_ack(options['device'], tlv.seq)

        #todo vyresit fragmentaci
        if tlv.fc.isfrag:
            raise Exception("NOT IMPLEMENTED YET")

        self.btc_blufi_protocol_handler(tlv, options['device'])

    def btc_blufi_protocol_handler(self, tlv, devid):
        #TODO vyresit assembling paketu
        if (not devid in self.devices): 
            return False

        if tlv.type.type == BLUFI_TYPE_CTRL:
            if 0: print('ctrl', tlv)
            if tlv.type.subtype == BLUFI_TYPE_CTRL_SUBTYPE_DISCONNECT_BLE:
                async_tools.add_timer_ms(100, lambda: self.handle_disconnect(devid))
            if tlv.type.subtype == BLUFI_TYPE_CTRL_SUBTYPE_GET_VERSION:
                self.blufi_send_encap(devid, FrameType(type=BLUFI_TYPE_DATA, subtype=BLUFI_TYPE_DATA_SUBTYPE_REPLY_VERSION), [BTC_BLUFI_GREAT_VER,BTC_BLUFI_SUB_VER])
            elif tlv.type.subtype == BLUFI_TYPE_CTRL_SUBTYPE_GET_WIFI_STATUS:
                activeSSID, isConnected = self.wifi.GetWifiStatus()
                self.blufi_send_wifistatus(devid, activeSSID, isConnected)
            elif tlv.type.subtype == BLUFI_TYPE_CTRL_SUBTYPE_GET_WIFI_LIST:
                self.wifi.InitiateScan()
                self.scantries = 100
                async_tools.add_timer_ms(100, lambda: self.handle_wifiscan(devid)) #check for wifi scan results
                pass
            elif tlv.type.subtype == BLUFI_TYPE_CTRL_SUBTYPE_SET_WIFI_OPMODE:
#                0x00: NULL；0x01: STA; 0x02: SoftAP; 0x03: SoftAP&STA.
                print('set wifi mode', tlv.data)
            elif tlv.type.subtype == BLUFI_TYPE_CTRL_SUBTYPE_CONN_TO_AP:
                self.wifi.Connect()
                self.devices[devid].wifistate_tries_remain = 2*10 #15 wait up to 15 seconds for wifi state change
                async_tools.add_timer_ms(500, lambda: self.handle_wificonnectstate(devid))
               
        elif tlv.type.type == BLUFI_TYPE_DATA:
            if 0: print('data', tlv)
            if tlv.type.subtype == BLUFI_TYPE_DATA_SUBTYPE_STA_SSID:
                self.wifi.config['SSID'] = tlv.data
            elif tlv.type.subtype == BLUFI_TYPE_DATA_SUBTYPE_STA_PASSWD:
                self.wifi.config['Passphrase'] = tlv.data
            elif tlv.type.subtype == BLUFI_TYPE_DATA_SUBTYPE_CUSTOM_DATA:
                if self.on_customdata:
                    self.on_customdata(tlv.data)

    def handle_wificonnectstate(self, devid):
        if (not devid in self.devices): 
            return False

        self.devices[devid].wifistate_tries_remain = self.devices[devid].wifistate_tries_remain - 1
        activeSSID, isConnected = self.wifi.GetWifiStatus()
        print('check wifi connect state',self.devices[devid].wifistate_tries_remain, activeSSID, isConnected)
        if (isConnected):
            self.blufi_send_wifistatus(devid, activeSSID, isConnected)
            return False

        elif self.devices[devid].wifistate_tries_remain == 0:
            self.blufi_send_wifistatus(devid, activeSSID, isConnected)

        return self.devices[devid].wifistate_tries_remain > 0

    def handle_wifiscan(self, devid):
        self.scantries -= 1
        if (self.scantries == 0): #timeout
            self.blufi_send_encap(devid, FrameType(type=BLUFI_TYPE_DATA, subtype=BLUFI_TYPE_DATA_SUBTYPE_WIFI_LIST), [])

        aplist = self.wifi.CheckScanResult()
        if (aplist is not None):
            pkt = b''
            for rec in aplist:
                ssid, rssi = rec['SSID'], rec['RSSI']
                pkt += ApRecord(length=len(ssid)+1, ssid=ssid, rssi=rssi).pack()

            self.blufi_send_encap(devid, FrameType(type=BLUFI_TYPE_DATA, subtype=BLUFI_TYPE_DATA_SUBTYPE_WIFI_LIST), pkt)
            self.scantries = 0

        #print('handle', devid,  (devid in self.devices) , (self.devices[devid].device.connected) , (self.scantries>0))
        return (devid in self.devices) and (self.devices[devid].device.connected) and (self.scantries>0)

    def handle_disconnect(self, devid):
        if devid in self.devices:
            dev = self.devices[devid].device
            if dev.connected:
                try:
                    dev.disconnect()
                except:
                    pass
            del self.devices[devid]
        return False

    def blufi_send_wifistatus(self, devid, activeSSID, isConnected):
        if (activeSSID is None) or len(activeSSID) == 0: 
            #not connected
            self.blufi_send_encap(devid, FrameType(type=BLUFI_TYPE_DATA, subtype=BLUFI_TYPE_DATA_SUBTYPE_WIFI_REP), [0, 0 if isConnected else 1,0]) #NULL (Not connected)
        else: 
            #connected to activeSSID
            pkt = bytes([1, #mode station
                         0 if isConnected else 1, #0 connected, 1 disconnected
                         0, 
                         BLUFI_TYPE_DATA_SUBTYPE_STA_SSID, 
                         len(activeSSID)
                         ]) + activeSSID
            self.blufi_send_encap(devid, FrameType(type=BLUFI_TYPE_DATA, subtype=BLUFI_TYPE_DATA_SUBTYPE_WIFI_REP), pkt) #STA connected

    def blufi_send_ack(self, devid, seq):
        self.blufi_send_encap(devid, FrameType(type=BLUFI_TYPE_CTRL, subtype=BLUFI_TYPE_CTRL_SUBTYPE_ACK), [seq])

    def blufi_send_encap(self, devid,  type, data):
        if (not self.characteristic) or (not devid in self.devices):
            return
        state = self.devices[devid]
        total = len(data)
        assert total < 65535

        #print('data to send', data)
        first, remain = True, total
        while (remain>0) or first:
            tlv = BluFiPacket()
            tlv.fc.datadir = BLUFI_FC_DIR_E2P
            tlv.type = type
            tlv.seq = state.sendseq

            ofs = total - remain
            if (remain > state.frag_size):
                #print('fragment', bytes(data[ofs:ofs+self.frag_size]))
                tlv.data = bytes([remain & 0xFF, (remain >> 8) & 0xFF]) + bytes(data[ofs:ofs+state.frag_size])
                tlv.fc.isfrag = True
                remain -= state.frag_size
            else:
                #print('no fragment', bytes(data[ofs:]))
                tlv.data = bytes(data[ofs:])
                remain = 0

            tlv.length = len(tlv.data)

            #if 1: print('respond',tlv.pack())
            
            #Bluez does not have API for sending notification to a particular device
            #this is broadcast
            self.characteristic.set_value(tlv.pack())

            first = False
            state.sendseq += 1
  

    @report_exception
    def notify(self, notifying, characteristic):
        if DEBUG: print('notify',notifying, characteristic)
        if notifying:
            self.characteristic = characteristic
        else:
            self.characteristic = None

    def send_custom_data(self, data, devid=None):
        for dev in self.devices:
            if dev == devid or devid is None:
                self.blufi_send_encap(dev, FrameType(type=BLUFI_TYPE_DATA, subtype=BLUFI_TYPE_DATA_SUBTYPE_CUSTOM_DATA), bytes(data))



if __name__ == '__main__':
    pkt = BluFiPacket.unpack(bytes([77, 0, 0, 4, 89, 121, 102, 103]))
    print(pkt)

    pkt = BluFiPacket.unpack(bytes([1, 0, 1, 3, 0, 1, 7]))
    print(pkt)

    pkt = BluFiPacket.unpack(bytes([1, 0, 2, 8, 1, 0, 128, 207, 92, 245, 195, 132, 25, 167, 36, 149, 127, 245, 221, 50, 59, 156, 69, 195, 205, 210, 97, 235, 116, 15, 105, 170, 148, 184, 187, 26, 92, 150, 64, 145, 83, 189, 118, 178, 66, 34, 208, 50, 116, 228, 114, 90, 84, 6, 9, 46, 158, 130, 233, 19, 92, 100, 60, 174, 152, 19, 43, 13, 149, 247, 214, 83, 71, 198, 138, 252, 30, 103, 125, 169, 14, 81, 187, 171, 95, 92, 244, 41, 194, 145, 180, 186, 57, 198, 178, 220, 94, 140, 114, 49, 228, 106, 167, 114, 142, 135, 102, 69, 50, 205, 245, 71, 190, 32, 201, 163, 250, 131, 66, 190, 110, 52, 55, 26, 39, 192, 111, 125, 192, 237, 221, 210, 248, 99, 115, 0, 1, 2, 0, 128, 164, 201, 163, 202, 173, 179, 254, 153, 22, 239, 115, 56, 80, 0, 49, 240, 39, 72, 46, 154, 68, 14, 217, 158, 221, 186, 35, 65, 153, 252, 62, 76, 234, 78, 125, 9, 54, 170, 241, 13, 165, 82, 171, 232, 22, 105, 248, 112, 57, 211, 253, 110, 125, 157, 163, 14, 27, 253, 215, 196, 132, 220, 220, 61, 176, 227, 211, 160, 60, 126, 176, 65, 232, 49, 5, 146, 52, 115, 110, 169, 167, 236, 187, 230, 130, 187, 7, 173, 107, 190, 23, 219, 159, 169, 142, 135, 98, 203, 160, 37, 245, 141, 8, 67, 66, 214, 192, 21, 104, 137, 57, 219, 214, 46, 91, 88, 46, 184, 135, 104, 26, 113, 148, 32, 214, 61, 199, 139]))
    print(pkt)

    ssid = b'SSID'
    pkt = ApRecord(length=len(ssid)+1, ssid=ssid, rssi=-123)
    print(pkt.pack())
    #xxx

    pkt = BluFiPacket()
    pkt.fc.datadir = BLUFI_FC_DIR_E2P
    pkt.type.type = BLUFI_TYPE_CTRL_SUBTYPE_ACK
    pkt.type.subtype = BLUFI_TYPE_CTRL_SUBTYPE_ACK
    pkt.seq = 1
    pkt.length = 4
    pkt.data = b'abcd'
    print(pkt)
    print(pkt.pack())
    print('ft',FrameType(type=BLUFI_TYPE_CTRL, subtype=BLUFI_TYPE_CTRL_SUBTYPE_ACK))
