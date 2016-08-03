"""
"""
import os
import sys
import time
import pickle
import socket
import select
import __main__
import datetime

from any import Any
"""------------------------------------------------------------*
    Declare
#------------------------------------------------------------"""
default_port = 21643
default_buff = 65536
max_buffer_len = 7
_ = Any(Any)
"""------------------------------------------------------------*
    Classes
#------------------------------------------------------------"""

class client(object):
    def __init__(self,SOCK=None,PORT=default_port):
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

    def auto_connect(self):
        cast = ('<broadcast>', self.auto_port)
        broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast.settimeout(2)
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        broadcast.sendto(__main__.__file__, cast)

        try:
            (svr_hostname,svr_port) = broadcast.recvfrom(self.recv_buffer)
        except:
            print "no server"
            sys.exit()

        broadcast.close()

        print('server says', svr_hostname,svr_port)
        # self.attach( svr_port[0], svr_port[1])
        self.attach( svr_hostname, svr_port[1])
        return self

    def attach(self,svr_host,svr_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("connect: %s :%s" % (svr_host, svr_port))
        self.sock.connect((svr_host, svr_port))
        return self.sock

    def wait(self,query,timeout):
        self.sock.setttimeout(timeout)

    def check(self,query,timeout):
        clock = 0
        interval = 6
        while clock < timeout:
            print()
            clock += interval
            time.sleep(interval)
            if not self.read(query, block=False):
                print("Message was processed")
                return True
        self.pull(query)
        print("Message Timed out!")
        return False

    def post(self,message):
        return self.reply(False,_,_,message)

    def pull(self, qry_message, block=True, erase=True):
        self.reply(True, block,erase, qry_message)
        return self.receive()

    def read(self, qry_message, block=True, erase=False):
        # print('read')
        self.reply(True,block,erase,qry_message)
        # print('/read')
        return self.receive()

    def reply(self, query, block, erase, payload):
        # print('reply')
        pickled_payload = pickle.dumps((query,block,erase,payload))
        self.xmit(self.sock, pickled_payload)
        # print('/reply')

    def receive(self):
        # print('receive')
        try:
            return pickle.loads(self.xrcv(self.sock))
        except:
            print( "server isn't speaking to us!" )
        # print('/receive')

    def xmit(self, sock, message):
        # print('xmit')
        sock.send(message)
        sock.recv(2)    # token reply, flushes buffer
        # print '/xmit'

    def xrcv(self, sock):
        # print('xrcv', self.recv_buffer)
        data = sock.recv(self.recv_buffer)
        # print(data)
        sock.send('ok')
        # print('/xrcv')
        return data


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
    print 0
    cfd.post((1,2,3,'hello'))
    print 5

    x = cfd.read((1,2,3,_))
    print('goodbye', x)
    # print(cfd.read('hello'))


"""------------------------------------------------------------*
    End of File
#------------------------------------------------------------"""
