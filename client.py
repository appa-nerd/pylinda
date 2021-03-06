"""
Title       pylinda/client
Version     1.0
Author      appa
Purpose


"""
import os
import sys
import time
import struct
import pickle
import socket
import select
import __main__
import datetime

"""------------------------------------------------------------*
    Declare
#------------------------------------------------------------"""
default_port = 21643
default_buff = 65536
# default_buff = 1024
max_buffer_len = 7



"""------------------------------------------------------------*
    Classes
#------------------------------------------------------------"""

class client(object):
    def __init__(self,SOCK=None,PORT=default_port):
        from pylinda.any import Any
        self.recv_buffer = default_buff
        self.auto_port = int(PORT)
        self.auto_addr = ("0.0.0.0", self.auto_port)
        self.host = socket.gethostname()
        self.local = socket.gethostbyname(self.host)
        self.debug = True
#         self.me = os.path.basename(__main__.__file__)
        self.sock = SOCK

    @property
    def now(self):
        return datetime.datetime.utcnow()

    def auto_connect(self, target='<broadcast>'):
        cast = (target, self.auto_port)
        broadcast = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM) #socket.SOCK_STREAM) #
        broadcast.settimeout(5)
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        #broadcast.sendto(__main__.__file__, cast)
        my_name_is = __main__.__file__

        broadcast.sendto(__main__.__file__.encode('utf-8'), cast)  # broadcast executing program's filename.

        try:
            (client_port,svr_port) = broadcast.recvfrom(self.recv_buffer)
            print(client_port)
        except Exception as msg:
            print("no server", msg)
            sys.exit()

        broadcast.close()
        # self.attach( svr_hostname, svr_port[1])
        self.attach( svr_port[0], svr_port[1])
        #self.attach( svr_port[0], int(client_port))
        return self

    def attach(self,svr_host,svr_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # TCP....
        print("connect: %s :%s" % (svr_host, svr_port))
        self.sock.connect((svr_host, svr_port))
        return self.sock

    def wait(self,query,timeout):
        self.sock.setttimeout(timeout)

    def post(self,message):
        # post tuple
        return self.reply(message,'POST')

    def in_b(self,message):
        # read blocking
        self.reply(message,'IN_B')
        return self.receive()

    def in_n(self,message):
        # in non-blocking (bool)
        self.reply(message,'IN_N')
        return self.receive()

    def rd_b(self,message):
        # read blocking
        self.reply(message,'RD_B')
        return self.receive()

    def rd_n(self,message):
        # read non-blocking (bool)
        self.reply(message,'RD_N')
        return self.receive()

    def reply(self, message, cmd):
        try:
            pickled_payload = pickle.dumps((message,cmd))
            header = struct.pack('!I', len(pickled_payload))
            self.sock.send(header)
            bytes = self.sock.send(pickled_payload)
        except KeyboardInterrupt:
            print("user disconnect!")
            sys.exit()


    def receive(self):
        '''
        Max recieve is 8k, so for larger loads you need to
        keep reading.
        '''
        try:
            header = self.sock.recv(4)
            # print(header,'?')
            buff, = struct.unpack('!I', header)
            my_buffer = 0
            my_buff = int(buff)
            data = b''
            while len(data) < int(buff):
                data += self.sock.recv(my_buff)
                my_buff = int(buff) - len(data)

            return pickle.loads(data)
        except KeyboardInterrupt:
            print("user disconnect!")
            sys.exit()
        except:
            print('dead packet?')

"""------------------------------------------------------------*
    Main
#------------------------------------------------------------"""

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("use: ./linda.py <server/client> <port>")
    if len(sys.argv) >= 2:
        port = sys.argv[1]
    else:
        port = default_port
    print('hello')
    cfd = client(PORT=port).auto_connect()
    cfd.post((1,2,3,'hello'))

    print('pull')
    y = cfd.in_b((1,2,3,_))
    # y = cfd.pull((1,2,3,_))

    print('goodbye', y)
    # cfd.read('bye')
    # print(cfd.read('hello'))


"""------------------------------------------------------------*
    End of File
#------------------------------------------------------------"""
