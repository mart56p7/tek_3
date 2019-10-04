import socket
import time
from threading import Thread
import json

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
with open(configfile) as fp:
    line = fp.readline()
    while line != "":
        cmdval = line.split(":", 1)
        if cmdval[0].strip() in settings:
            settings[cmdval[0].strip()] = (int)(cmdval[1].strip());
        line = fp.readline()

# Prints the current client settings
print("Current client settings loaded from ", configfile)
for cmd, val in list(settings.items()):
    print(cmd, ":", val)

def send(msg, recaddress):
    global sock
    return sock.sendto(msg.encode('ascii'), sendaddress)

# Controls that no more than a given number of packages can be send from client
# Returns true if we are allowed to accept the package, false otherwise
def acceptPackage(address):
    global settings, clients
    if settings["MaxPackages"] > 0:
        # Cleanup packages from client
        for t1, t2 in list(clients[address]["packages"].items()):
            if time.time() - t2 > 1:
                clients[address]["packages"].pop(t1)
        # Count packages from client
        packlen = len(clients[address]["packages"]) + 1
        print("Packages", packlen)
        if packlen <= settings["MaxPackages"]:
            print("Accepting package", time.time())
            clients[address]["packages"][str(packlen) + '_' + str(time.time())] = time.time()
            return True
        else:
            print("Rejecting packages", time.time())
            return False
    else:
        clients[address]["packages"][str(packlen) + '_' + str(time.time())] = time.time()
        return False

def connectionTimeout():
    global clients, sock
    while True:
        print(json.dumps(clients))
        if len(clients) > 0:
            for address, client in list(clients.items()):
                print(time.time())
                print(address)
                print(client)
                if time.time() - client['time'] >= 4:
                    client['locked'] = 1
                    # Reset connection
                    print("Reset connection")
                    # Used incase of localhost connection
                    saddress = (address, client['port'])
#                    print("saddress", saddress[0], saddress[1], type(saddress))
                    send("con-res 0xFE", saddress)
                    clients.pop(address)
                    client['locked'] = 0
                else:
                    print("Do nothing")
        print("checking client")
        time.sleep(1)

# timeout manager
timeoutmanager = Thread(target=connectionTimeout, args=[])
timeoutmanager.start()

while True:
    try:
        data, sendaddress = sock.recvfrom(4096)
        strdata = data.decode("utf-8")
        # Used incase of localhost connection
        if sendaddress[0] == "127.0.0.1":
            address = IPAddr
        else:
            address = sendaddress[0]
        answer = ""
        print(clients)
        if strdata.startswith("com-0 "):
            if(strdata == "com-0 accept") and address in clients: # only continueing if a connecting is in progress to ip adress given in first handshake
                clients[address] = {"time" : time.time(), "state" : "connected", "msgnum" : 0, "port" : sendaddress[1], "locked" : 0, "packages" : {} }

            else: #A client can at restart the state of a connection
                cip = strdata[len("com-0 "):len(data)]
                print(cip, address[0])
                try:
                    socket.inet_aton(cip)
                    clients[cip] =  {"time" : time.time(), "state" : "connecting", "msgnum" : 0, "port" : sendaddress[1], "locked" : 0, "packages" : {} }
                    print('\tReceived welcome msg from', cip)
                    answer = "com-0 accept " + IPAddr
                except socket.error:
                    print("Invalid ip address given from ", address, cip)
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
                    clients[address]["time"] = time.time()
                elif strdata == "con-h 0x00": #Refresh connection timer
                    clients[address]["time"] = time.time()
                    clients[address]["packages"][time.time()] = time.time();
                elif strdata != "con-res 0xFF":
                    # Unknown command resetting connection
                    clients.pop(address)
                    answer = "con-res 0xFE"
                else:
                    # Do nothing
                    pass
            if address in clients:
                clients[address]['locked'] = 0

        if len(answer) > 0:
    #        print("sendadress", sendaddress[0], sendaddress[1], type(sendaddress))
            sent = send(answer, sendaddress)
            print('sent {} bytes back to {}'.format(sent, sendaddress), answer)
    except:
        print("Caught exception")