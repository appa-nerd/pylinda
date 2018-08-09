"""
Title       Pylinda Module

Version     0.1
Author      appa
Purpose


"""

"""------------------------------------------------------------*
    Declare
#------------------------------------------------------------"""
default_port = 21643
default_buff = 65536
max_buffer_len = 256

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
    Classes
    _ = Any(Any)
    _int = Any(int)
#------------------------------------------------------------"""
class Any(object):
    def __init__(self,Type):
        if type(Type) == type:
            self.my_type = Type
        else:
            self.my_type = type(Type)

    def __eq__(self,other):
        if self.my_type == Any:
            return True
        elif type(other) == self.my_type:
            return True
        else:
            return False
"""------------------------------------------------------------*
    Pylinda Server
#------------------------------------------------------------"""
class server(object):
    _ = Any(Any)
    _dt = Any(datetime)

    def __init__(self,PORT=default_port):
        self.recv_buffer = default_buff
        self.auto_port = int(PORT)
        self.server_port = 8048
        # self.server_addr = ("0.0.0.0", self.server_port)
        self.auto_addr = ("0.0.0.0", self.auto_port)
        self.host = socket.gethostname()
        self.debug = False
        #self.tuple_db = {'BLOCK':[], 'POST':[]}
        self.block = {}
        self.post = {}
        self.connections = {}
        self.setup()
        self.activate = True
        self.service()

    @property
    def now(self):
        return datetime.datetime.utcnow()

    def setup(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        # self.server_socket.bind(('',self.server_port))    # use the hostname :(
        self.server_socket.bind(('',self.auto_port))    # use the hostname :(
        self.server_socket.listen(5)   # might be important, but it appears the clients are connecting fine.

        self.auto_socket = socket.socket(socket.AF_INET, # internet
                                            socket.SOCK_DGRAM) # UDP # socket.SOCK_STREAM) # TCP :
        print('auto addr', self.auto_addr)
        self.auto_socket.bind(self.auto_addr)

        self.connections[self.server_socket] = (self.host, 'server_socket')
        self.connections[self.auto_socket] = (self.host, 'auto_socket')

    def deregister(self, sock):
        # remove any blocking tuples for <socket>
        #[self.tuple_db['BLOCK'].pop(self.tuple_db['BLOCK'].index(x)) for x in self.tuple_db['BLOCK'] if x[1] == sock]
        del self.connections[sock]
        sock.close()

    def service(self):
        while self.activate:
            read_list, write_list, exe_list = select.select(self.connections.keys(),[],[])
            #self.report()
            que = len(read_list)
            if que > 1:
                print('queue: %s' % len(read_list))
            for sock in read_list:
                try:
                    if sock == self.auto_socket:    #broadcast socket
                        (process_name,fd) = sock.recvfrom(self.recv_buffer)
                        print( "Autosocket:", process_name)
                        sock.sendto(str(self.server_port).encode('utf-8'),fd)
                    elif sock == self.server_socket:    # connection request
                        client, addr = self.server_socket.accept()
                        print("Serversocket: %s" % client)
                        self.connections[client] = (addr, client)
                    else: #if sock:
                        try:
                            data = self.recv(sock)  # recieve method!
                            if data:
                                self.command(data,sock)
                        except Exception as msg:
                            print( "Socket Error: %s" % msg)
                            self.deregister(sock)
                            sock.close()
                        self.report()
                except Exception as msg:
                    print("Server exception: %s" % msg)

        # shutdown server
        for x in self.connections:
            if x == self.server_socket:
                continue
            self.server_socket.close()


    def reply(self,sock,term):
        pickled_payload = pickle.dumps(term)
        header = struct.pack('!I', len(pickled_payload))
        sock.send(header)
        sock.send(pickled_payload)

        # sock.send(pickle.dumps(term))

    def recv(self,sock):
        header = sock.recv(4)
        buff, = struct.unpack('!I', header)
        # print('buffer: %s' % buff)
        my_buff = int(buff)

        data = b''
        while len(data) < int(buff):
            new_data = sock.recv(my_buff)
            if new_data:
                data += new_data
            else:
                print('client quit!')
                return False

            my_buff = int(buff) - len(data)
            sys.stdout.flush()

        return pickle.loads(data)

    def shutdown(self):
        self.activate = False

    def command(self, command_tuple, sock):
        '''
        (data, linda_cmd)
        POST
        IN_B    (blocking)
        IN_N    (non-blocking)
        RD_B
        RD_N
        <new> WATCH - block for only new tuples (not existing)
        '''
        print('cmd',command_tuple)
        print('post',self.post)
        print('block',self.block)
        (hash, linda_cmd) = command_tuple

        if linda_cmd == "shutdown":
            print('shutdown')
            self.shutdown()
            return

        if linda_cmd == 'POST':
            '''
            if nothing is blocked, add to post list
            if block is RD, add to post list
                return data to send_sock.
            '''
            hash, data = hash
            blocked = self.block.get(hash,[])
            if blocked == []:
                self.post[hash] = self.post.get(hash,[]) + [data]
            else:
                send_sock, cmd = self.block.get(hash,[]).pop()
                self.reply(send_sock, data)
                if cmd == 'RD':  # for reads, post the data.
                    self.post[hash] = self.post.get(hash,[]) + [data]
            return



        if linda_cmd == 'WATCH':
            # Wait for new tuples, Blocking
            # destructive.
            self.block[hash] = self.block.get(hash,[]) + [(sock,'IN')]
            return

        if linda_cmd == 'IN_B':
            # Pull in, Blocking
            found = self.post.get(hash,[])   # returns data
            if found == []:
                self.block[hash] = self.block.get(hash,[]) + [(sock,'IN')]
            else:
                data = self.post[hash].pop()
                self.reply(sock,data) # found[0][1] -->
            return

        if linda_cmd == 'IN_N':
            # Pull in, Non-blocking
            #found = self.post.pop(hash,[])   # returns data
            found = self.post.get(hash,[])
            if found == []:
                self.reply(sock,False)
            else:
                data = self.post[hash].pop()
                self.reply(sock,data)
            return

        if linda_cmd == 'RD_B':
            # Read, Blocking
            found = self.post.get(hash,[])
            if found == []:
                self.block[hash] = self.block.get(hash,[]) + [(sock,'RD')]
            else:
                data = self.post[hash][0]
                self.reply(sock,data)

            return

        if linda_cmd == 'RD_N':
            # Read, Non-blocking
            found = self.post.get(hash,[])
            if found == []:
                self.reply(sock,False)
            else:
                data = self.post[hash][0]
                self.reply(sock,data)
            return

    def report(self):
        if self.debug:
            for key in self.tuple_db:
                if key:
                    title = "Queries"
                else:
                    title = "Posts"
                print("-| Query: [%s]" % title)
                for record in self.tuple_db[key]:
                    print("|\t%s" %(str(record[1])[:100]))
            print("-\_" + '_'*50)
            '''
            for x in self.connections:
                addr, p = self.connections[x]
                print("|\t%s [%s]" % (p,addr))
            '''
            print("Connection=%s" % len(self.connections))
"""------------------------------------------------------------*
    Pylinda Client
#------------------------------------------------------------"""
class client(object):
    _ = Any(Any)
    _dt = Any(datetime)

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

    def auto_connect(self, target='<broadcast>'):
        cast = (target, self.auto_port)
        broadcast = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM) #socket.SOCK_STREAM) #
        broadcast.settimeout(5)
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        #broadcast.sendto(__main__.__file__, cast)
        #my_name_is = __main__.__file__

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

    def post(self,hash,message):
        # post tuple
        return self.reply((hash,message),'POST')

    def watch(self,message):
        self.reply(message,'WATCH')
        return self.recieve()

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

def function_test():
    print('do something clever here...')

"""------------------------------------------------------------*
    Main
#------------------------------------------------------------"""




"""------------------------------------------------------------*
    Junk
#------------------------------------------------------------"""
