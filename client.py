import socket
import time
from threading import Thread
import select

class Client:
    # timeout in seconds
    timeout = 1.1
    # Create a UDP socket
    sock = None
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
    # number of messages that are send
    messages = 0
    # name, which is IP:port
    name = ""
    # debug information
    debug=True
    def msgout(self, msg, func=None):
        if self.debug:
            if func is None:
                print(str(round(time.time(), 1)) + ": " + self.name + " > " + msg)
            else:
                print(str(round(time.time(), 1)) + ": " + self.name + " > " + "\t" + func + " > " + msg)

    def __init__(self, port=45000, msges=25):
        self.msgout("Init", "init")
        self.messages = msges + 1
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", port))
        self.name = self.address + ":" + str(port)
        with open(self.configfile) as fp:
            line = fp.readline()
            while line != "":
                cmdval = line.split(":", 1)
                if cmdval[0].strip() in self.settings:
                    self.settings[cmdval[0].strip()] = (cmdval[1].strip() == "True");
                line = fp.readline()

        # self.msgouts the current client settings
        self.msgout("Current client settings loaded from " + self.configfile, "init")
        for cmd, val in list(self.settings.items()):
            self.msgout(cmd + ":" + str(val), "init")
        if self.settings["KeepALive"]:
            self.msgout("Keep alive running..", "init")
            keepalive = Thread(target=self.KeepAlive)
            keepalive.start()
        self.msgout("talking to server", "init")
        # Lets talk to our server!
        try:
            # Making the handshake
            message = 'com-0 ' + self.address
            self.send(message)
            rdata = self.receive()
            self.msgout("com-0 accept " + self.address + " " + rdata, "init")
            if self.constatus == "connecting":
                if rdata == ("com-0 accept " + self.address):
                    self.msgout("Connected", "init")
                    self.constatus = "connected"
                    self.send("com-0 accept")

                for i in range(1, self.messages):
                    if self.constatus == "connected":
                        if self.msgnum == 0:
                            self.send("msg-0=hello, i am a new user")
                        elif rdata == "res-"+str(self.msgnum)+"=I am server":
                            self.msgnum = self.msgnum + 1
                            self.send("msg-"+str(self.msgnum)+"=Ok, good to know")
                        self.msgnum = self.msgnum + 1
                        rdata = self.receive()
                        while rdata is None:
                            # Resend
                            self.msgout("Resending data", "init")
                            if self.msgnum == 0:
                                self.send("msg-0=hello, i am a new user")
                            else:
                                self.send("msg-" + str(self.msgnum-1) + "=Ok, good to know")
                            self.msgout("Waiting for data", "init")
                            if self.timeout > 5:
                                raise Exception("Timeout")
                            rdata = self.receive()
                # Sending unknown command to server, that forces a close
            if not self.settings["KeepALive"]:
                rdata = None
                while rdata is None:
                    self.send("close")
                    rdata = self.receive()


        except Exception as errmsg:
            self.msgout("Exception: " + str(errmsg), "init")
        finally:
            if not self.settings["KeepALive"]:
                self.msgout('closing socket', "init")
                self.sock.close()
                self.msgout("Client msg exchange completed, closing connection", "init")
            else:
                self.msgout("Client msg exchange completed - running keepalive", "init")



    # Function used for heartbeat
    def KeepAlive(self):
        while True:
            if time.time() - self.lasttransmission > 3 and self.constatus == "connected":
                self.msgout("Sending KeepALive", "KeepAlive")
                self.send("con-h 0x00")
            time.sleep(0.1)



    # Default function to send messages to the server
    def send(self, msg):
        self.lasttransmission = time.time()
        self.msgout(msg, "send")
        sent = self.sock.sendto(bytes(msg, 'utf-8'), self.server_address)

    # Default function to receive messages. If the connection to the server is closed by server this method raises a exception, else the message is returned
    def receive(self):
        #data, server = sock.recvfrom(4096)
        # ref https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method/25533241
        self.msgout("Waiting for data", "receive")
        rdata = None
        ready = select.select([self.sock], [], [], self.timeout)
        if ready[0]:
            data = self.sock.recv(4096)
            rdata = data.decode("utf-8")
            self.msgout("Received = " + rdata, "receive")
        else:
            self.msgout("Waiting, timeout increased to " + str(self.timeout), "receive")
        if rdata == "con-res 0xFE":
            self.send("con-res 0xFF")
            self.constatus = "connecting"
            raise Exception("\t\treceive: Connection forcefully closed by server")
        return rdata



def clt(port, messages):
    a = Client(port, messages)

t1 = Thread(target=clt, args=[45000, 20])
t2 = Thread(target=clt, args=[45001, 50])
t3 = Thread(target=clt, args=[45002, 100])
t4 = Thread(target=clt, args=[45003, 1000])
t5 = Thread(target=clt, args=[45004, 5])
t6 = Thread(target=clt, args=[45005, 1])
t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()


t1.join()
t2.join()
t3.join()
t4.join()
t5.join()
t6.join()