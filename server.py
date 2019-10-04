import socket
import time
from threading import Thread
import json

#START#############################
#START#### SETTINGS ###############
#START#############################
debug=False
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = ('localhost', 10000)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)
clients = {}
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
# Default settings
settings = {"MaxPackages" : 25}

# Loads settings from configfile into our settings dictionary, overriding default settings
configfile = 'server.ini'

#END###############################
#END###### SETTINGS ###############
#END###############################

#START#############################
#START#### FUNCTIONS ##############
#START#############################

def send(msg, recaddress):
    global sock, clients, debug
    result = None
    try:
        result = sock.sendto(msg.encode('ascii'), sendaddress)
    except:
        if debug: print("\tsend: Closing connection to " + sendaddress[0] + ":" + str(sendaddress[1]))
        clients.pop(sendaddress[0] + "_" + str(sendaddress[1]))
    return result

# Controls that no more than a given number of packages can be send from client
# Returns true if we are allowed to accept the package, false otherwise
# This method also sets when we have last communicated with a client
def acceptPackage(address):
    global settings, clients
    # Count packages from client
    packlen = len(clients[address]["packages"]) + 1
    if settings["MaxPackages"] > 0:
        # Cleanup packages from client
        for t1, t2 in list(clients[address]["packages"].items()):
            if time.time() - t2 > 1:
                clients[address]["packages"].pop(t1)
        if debug: print("\tacceptPackage: Packages", packlen)
        if packlen <= settings["MaxPackages"]:
            if debug: print("\tacceptPackage: Accepting package", time.time())
            clients[address]["packages"][str(packlen) + '_' + str(time.time())] = time.time()
            clients[address]["time"] = time.time()
            return True
        else:
            if debug: print("\tacceptPackage: Rejecting packages", time.time())
            clients[address]["time"] = time.time()
            return False
    else:
        clients[address]["packages"][str(packlen) + '_' + str(time.time())] = time.time()
        return False

# Checks for connection timeout, and if connection timeout close connection to client
def connectionTimeout():
    global clients, sock
    while True:
        if debug: print(json.dumps(clients))
        if len(clients) > 0:
            for address, client in list(clients.items()):
                if time.time() - client['time'] >= 4:
                    client['locked'] = 1
                    # Reset connection

                    if debug: print("\tconnectionTimeout: Reset connection")
                    # Used incase of localhost connection
                    saddress = (address, client['port'])
                    send("con-res 0xFE", saddress)
                    closeConnection(address, " Due to timeout")
                    client['locked'] = 0
                else:
                    if debug: print("\tconnectionTimeout: Do nothing")
        # if debug: print("\tconnectionTimeout: checking client")
        time.sleep(0.1)

def closeConnection(address, msg):
    global clients
    if address in clients:
        print("\tcloseConnection: closed connection to " + address + " after " + str(round(clients[address]["msgnum"]/2)) + " messages." + msg)
        clients.pop(address)

#END###############################
#END###### FUNCTIONS ##############
#END###############################

#START#############################
#START#### CODE START #############
#START#############################

#Loading config file
with open(configfile) as fp:
    line = fp.readline()
    while line != "":
        cmdval = line.split(":", 1)
        if cmdval[0].strip() in settings:
            settings[cmdval[0].strip()] = (int)(cmdval[1].strip());
        line = fp.readline()

# Prints the current client settings
if debug: print("Current client settings loaded from ", configfile)
for cmd, val in list(settings.items()):
    if debug: (cmd, ":", val)

# timeout manager
timeoutmanager = Thread(target=connectionTimeout, args=[])
timeoutmanager.start()

while True:
    try:
        data, sendaddress = sock.recvfrom(4096)
        strdata = data.decode("utf-8")
        if debug: print("Received " + strdata)
        # Used incase of localhost connection
        if sendaddress[0] == "127.0.0.1":
            address = IPAddr + ":" + str(sendaddress[1])
        else:
            address = sendaddress[0] + ":" + str(sendaddress[1])
        answer = ""
        if debug: print(clients)
        if strdata.startswith("com-0 "):
            if(strdata == "com-0 accept") and address in clients: # only continueing if a connecting is in progress to ip adress given in first handshake
                print(address + " is now connected")
                clients[address] = {"time" : time.time(), "state" : "connected", "msgnum" : 0, "port" : sendaddress[1], "locked" : 0, "packages" : {} }

            else: #A client can at restart the state of a connection
                cip = strdata[len("com-0 "):len(data)]
                if debug: print(cip, address[0])
                try:
                    socket.inet_aton(cip)
                    clients[cip + ":" + str(sendaddress[1])] =  {"time" : time.time(), "state" : "connecting", "msgnum" : 0, "port" : sendaddress[1], "locked" : 0, "packages" : {} }
                    if debug: print('\tReceived welcome msg from', cip)
                    answer = "com-0 accept " + IPAddr
                except socket.error:
                    if debug: print("Invalid ip address given from ", address, cip)
        elif address in clients and (time.time() - clients[address]["time"]) < 4 and clients[address]['locked'] == 0:
            clients[address]['locked'] = 1
            if time.time() - clients[address]["time"] >= 4:
                # Makes sure that we are not terminating the connection while we are using it
                pass
            elif acceptPackage(address):
                if strdata.startswith("msg-"+str(clients[address]["msgnum"])+"="):
                    cmd = strdata[len("msg-"+str(clients[address]["msgnum"])+"="):len(data)]
                    # No matter what is send to us we answer I am server
                    answer = "res-"+str(clients[address]["msgnum"]+1)+"=I am server"
                    clients[address]["msgnum"] = clients[address]["msgnum"] + 2
                elif strdata == "con-h 0x00": #Refresh connection timer
                    # All logic is done in acceptPackage
                    pass
                elif strdata != "con-res 0xFF":
                    # Unknown command resetting connection
                    closeConnection(address, " Due to unknown command '" + strdata + "'")
                    answer = "con-res 0xFE"
                else:
                    # Do nothing
                    print("Do nothing")
                    pass
            if address in clients:
                clients[address]['locked'] = 0

        if len(answer) > 0:
    #        print("sendadress", sendaddress[0], sendaddress[1], type(sendaddress))
            sent = send(answer, sendaddress)
            if debug: print('sent {} bytes back to {}'.format(sent, sendaddress), answer)
    except ConnectionResetError as cre:
        print("Connection was badly closed by client")
    except Exception as e:
        print("Server crashed! Server has restarted..")

#END###############################
#END###### CODE ###################
#END###############################