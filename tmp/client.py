import socket
import time
from threading import Thread
import select



# timeout in seconds
timeout = 1
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(0)
# Gets the IP address for the client
address = socket.gethostbyname(socket.gethostname())
# The server we are connecting too
server_address = ('localhost', 10000)
# When last transmission was received
lasttransmission = time.time()
# The connection status
constatus = "connecting"
# The current message number
msgnum = 0


# Default settings
settings = {"KeepALive" : False}

# Loads settings from configfile into our settings dictionary, overriding default settings
configfile = 'client.ini'
with open(configfile) as fp:
    line = fp.readline()
    while line != "":
        cmdval = line.split(":", 1)
        if cmdval[0].strip() in settings:
            settings[cmdval[0].strip()] = (cmdval[1].strip() == "True");
        line = fp.readline()

# Prints the current client settings
print("Current client settings loaded from ", configfile)
for cmd, val in list(settings.items()):
    print(cmd, ":", val)

# Function used for heartbeat
def KeepAlive():
    global lasttransmission, constatus
    while True:
        if time.time() - lasttransmission > 3 and constatus == "connected":
            print("Sending KeepALive")
            send("con-h 0x00")
        time.sleep(0.4)

if settings["KeepALive"]:
    print("Keep alive running..")
    keepalive = Thread(target=KeepAlive, args=[])
    keepalive.start()

# Default function to send messages to the server
def send(msg):
    global soc, lasttransmission
    lasttransmission = time.time()
    print("Sending ", msg)
    sent = sock.sendto(bytes(msg, 'utf-8'), server_address)

# Default function to receive messages. If the connection to the server is closed by server this method raises a exception, else the message is returned
def receive():
    global timeout, sock

    #data, server = sock.recvfrom(4096)
    # ref https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method/25533241
    rdata = None
    ready = select.select([sock], [], [], timeout)
    if ready[0]:
        data = sock.recv(4096)
        rdata = data.decode("utf-8")
        timeout = max(timeout / 2, 1)
        print("Received", data)
    else:
        timeout = 2 * timeout
        print("Waiting, timeout increased to ", timeout)
    if rdata == "con-res 0xFE":
        send("con-res 0xFF")
        raise Exception("Connection forcefully closed by server")
    return rdata




# Lets talk to our server!
try:
    # Making the handshake
    message = 'com-0 ' + address
    send(message)
    rdata = receive()
    print("com-0 accept " + address, rdata)
    if constatus == "connecting":
        if rdata == ("com-0 accept " + address):
            print("Connected")
            constatus = "connected"
            send("com-0 accept")

        for i in range(1, 20):
            print("i = " + str(i), constatus, address)
            if constatus == "connected":
                if msgnum == 0:
                    send("msg-0=hello, i am a new user")
                elif rdata == "res-"+str(msgnum)+"=I am server":
                    msgnum = msgnum + 1
                    send("msg-"+str(msgnum)+"=Ok, good to know")
                msgnum = msgnum + 1
                rdata = receive()
                while rdata is None:
                    # Resend
                    if msgnum == 0:
                        send("msg-0=hello, i am a new user")
                    else:
                        send("msg-" + str(msgnum-1) + "=Ok, good to know")
                    print("Waiting for data")
                    if timeout > 10000:
                        raise Exception("Timeout")
                    rdata = receive()
        rdata = receive()
except Exception as errmsg:
    print("Error", errmsg)
finally:
    if not settings["KeepALive"]:
        print('closing socket')
        sock.close()

