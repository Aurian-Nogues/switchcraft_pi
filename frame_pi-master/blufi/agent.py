import dbus
from blufi.tools import report_exception

BUS_NAME = 'org.bluez'
AGENT_IFACE = 'org.bluez.Agent1'
AGENT_INTERFACE = 'org.bluez.Agent1'
AGNT_MNGR_IFACE = 'org.bluez.AgentManager1'
AGENT_PATH = '/zv/blufi/agent'
AGNT_MNGR_PATH = '/org/bluez'

def install_agent(agentClass,  adapter=None, cap=None):
    bus = dbus.SystemBus()
    agent = agentClass(bus, AGENT_PATH)
    agnt_mngr = dbus.Interface(bus.get_object(BUS_NAME, AGNT_MNGR_PATH), AGNT_MNGR_IFACE)
    try:
        agnt_mngr.UnregisterAgent(AGENT_PATH)
        print("Previous agent removed")
    except:
        pass
    agnt_mngr.RegisterAgent(AGENT_PATH, agent.CAPABILITY if cap is None else cap)
    agnt_mngr.RequestDefaultAgent(AGENT_PATH)

#see https://gist.github.com/studiofuga/249035dd86e1c7c7bb75

def ask(prompt):
    try:
        return raw_input(prompt)
    except:
        return input(prompt)

def set_trusted(path):
    props = dbus.Interface(dbus.SystemBus().get_object("org.bluez", path), "org.freedesktop.DBus.Properties")
    props.Set("org.bluez.Device1", "Trusted", True)
    
class Rejected(dbus.DBusException):
	_dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):
#    CAPABILITY = 'KeyboardOnly' #RequestPasskey
#    CAPABILITY = 'KeyboardDisplay' #RequestConfirmation
#    CAPABILITY = 'DisplayOnly' #RequestConfirmation
#    CAPABILITY = 'DisplayYesNo' #RequestConfirmation
    CAPABILITY = 'NoInputNoOutput' #RequestAuthorization
    exit_on_release = True

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        print("Release")
        #if self.exit_on_release:
        #    mainloop.quit()

    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print("AuthorizeService (%s, %s)" % (device, uuid))
        # authorize = ask("Authorize connection (yes/no): ")
        authorize="yes"
        if (authorize == "yes"):
            return
        raise Rejected("Connection rejected by user")

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        print("RequestPinCode (%s)" % (device))
        set_trusted(device)
        return "0000"
        # return ask("Enter PIN Code: ")

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print("RequestPasskey (%s)" % (device))
        set_trusted(device)
        # passkey = ask("Enter passkey: ")
        passkey = "0000"
        return dbus.UInt32(passkey)

    @dbus.service.method(AGENT_INTERFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        print("DisplayPasskey (%s, %06u entered %u)" % (device, passkey, entered))

    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        print("DisplayPinCode (%s, %s)" % (device, pincode))

    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print("RequestConfirmation (%s, %06d)" % (device, passkey))
        # confirm = ask("Confirm passkey (yes/no): ")
        confirm = "yes"
        if (confirm == "yes"):
            set_trusted(device)
            return
        raise Rejected("Passkey doesn't match")

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print("RequestAuthorization (%s)" % (device))
        # auth = ask("Authorize? (yes/no): ")
        auth = "yes"
        if (auth == "yes"):
            return
        raise Rejected("Pairing rejected")

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")



#Possibilities for pairing:
# DisplayOnly or DisplayYesNo : authentication by PIN/passkey code
# KeyboardOnly or KeyboardDisplay : yes/no choice to the pairing attempt
# NoInputNoOutput : no user confirmation

class AgentNoDisplayNoKeyboard(Agent):
    CAPABILITY = 'NoInputNoOutput'
    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print("RequestAuthorization (%s)" % (device))
        return
        #raise Rejected("Pairing rejected")

class AgentDisplayOnly(dbus.service.Object):
    CAPABILITY = 'DisplayOnly'

    # @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    # def RequestConfirmation(self, device, passkey):
    #     self.on_passkey(passkey)
    #     set_trusted(device)

    # @dbus.service.method(AGENT_INTERFACE, in_signature="ouq", out_signature="")
    # def DisplayPasskey(self, device, passkey, entered):
    #     self.on_passkey(passkey)

    # @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    # def DisplayPinCode(self, device, pincode):
    #     self.on_passkey(pincode)

    # def on_passkey(self, passkey):
    #     print("DisplayPasskey (%s, %06u entered %u)" % (device, passkey, entered))        
    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print("RequestAuthorization (%s)" % (device))
        return