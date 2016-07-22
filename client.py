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
            (port_string,server) = broadcast.recvfrom(self.recv_buffer)
        except:
            print "no server"
            sys.exit()
        print( 123, port_string, 'server:', server)

        broadcast.close()
        (svr_host, auto_port) = server
        print(svr_host, auto_port)
        self.attach( svr_host, auto_port)
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
        self.reply(True,block,erase,qry_message)
        return self.receive()

    def reply(self, query, block, erase, payload):
        pickled_payload = pickle.dumps((query,block,erase,payload))
        self.xmit(self.sock, pickled_payload)

    def receive(self):
        try:
            return pickle.loads(self.xrcv(self.sock))
        except:
            print( "server isn't speaking to us!" )

    def xmit(self, sock, message):
        sock.send(message)
        sock.recv(2)    # token reply, flushes buffer

    def xrcv(self, sock):
        data = sock.recv(self.recv_buffer)
        sock.send('ok')
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

    cfd = client(PORT=port).auto_connect()
    cfd.post('hello')
    print(cfd.pull('hello'))


"""------------------------------------------------------------*
    End of File
#------------------------------------------------------------"""
