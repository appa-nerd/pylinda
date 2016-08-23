"""
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

from any import Any
_ = Any(Any)
dt = Any(datetime.datetime)
"""------------------------------------------------------------*
    Declare
#------------------------------------------------------------"""
default_port = 21643
default_buff = 65536
#default_buff = 1024
max_buffer_len = 256

"""------------------------------------------------------------*
    Classes
#------------------------------------------------------------"""
class server(object):
    def __init__(self,PORT=default_port):
        self.recv_buffer = default_buff
        self.auto_port = int(PORT)
        self.server_port = 8048
        # self.server_addr = ("0.0.0.0", self.server_port)
        self.auto_addr = ("0.0.0.0", self.auto_port)
        self.host = socket.gethostname()
        self.debug = False
        self.tuple_db = {'BLOCK':[], 'POST':[]}
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
        [self.tuple_db['BLOCK'].pop(self.tuple_db['BLOCK'].index(x)) for x in self.tuple_db['BLOCK'] if x[1] == sock]
        del self.connections[sock]
        sock.close()

    def service(self):
        while self.activate:
            read_list, write_list, exe_list = select.select(self.connections.keys(),[],[])
            # self.report()
            que = len(read_list)
            if que > 1:
                print('queue: %s' % len(read_list))
            for sock in read_list:
                try:
                    if sock == self.auto_socket:    #broadcast socket
                        (process_name,fd) = sock.recvfrom(self.recv_buffer)
                        print( "Autosocket:", process_name)
                        sock.sendto(str(self.server_port),fd)
                    elif sock == self.server_socket:    # connection request
                        client, addr = self.server_socket.accept()
                        print("Serversocket: %s" % client)
                        self.connections[client] = (addr, process_name)
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
        print(header,'reply?')
        sock.send(header)
        sock.send(pickled_payload)

        # sock.send(pickle.dumps(term))

    def recv(self,sock):
        header = sock.recv(4)
        buff, = struct.unpack('!I', header)
        print('buffer: %s' % buff)

        my_buffer = 0
        data = ''
        while len(data) < int(buff):

            data += sock.recv(int(buff))
            print(len(data))
        # data = sock.recv(int(buff))
        return pickle.loads(data)

        # x = sock.recv(default_buff)
        # self.reply(sock,'')
        # return x

    def shutdown(self):
        self.activate = False

    def search_db(self, DB, match):
        # x <-- (sock,data)
        if DB == 'POST':
            found = [(self.tuple_db[DB].index(x),x) for x in self.tuple_db[DB] if match == x[1]]

        if DB == 'BLOCK':
            found = [(self.tuple_db[DB].index(x),x) for x in self.tuple_db[DB] if x[1] == match]
            # print(123, match, found)
            # for x in self.tuple_db[DB]:
            #     print('aa',x[1], match == x[1], x[1] == match)

        if found:
            idx, store = found[0]
            socket, data = store
            # print('-'*10)
            # print(found[0])
            # print('+'*10)
            return (idx,data,socket)
        else:
            return False

        # if match in self.tuple_db[DB]:
        #     return [(self.tuple_db[db_name].index(x),x) for x in self.tuple_db[db_name] if match == x] # [(idx,msg),]


    def command(self, command_tuple, sock):
        '''
        (data, linda_cmd)
        POST
        IN_B    (blocking)
        IN_N    (non-blocking)
        RD_B
        RD_N
        '''
        (data, linda_cmd) = command_tuple
        if linda_cmd == "shutdown":
            print('shutdown')
            self.shutdown()
            return

        # print(linda_cmd, data)
        if linda_cmd == 'POST':
            found = self.search_db('BLOCK',data)

            if found:
                (block_idx, return_data, send) = found
                self.tuple_db['BLOCK'].pop(block_idx) # found[0][0] --> index
                self.reply(send,data)
            else:
                self.tuple_db['POST'].append((sock,data))
            return

        if linda_cmd == 'IN_B':
            # Pull in, Blocking
            found = self.search_db('POST', data)
            if found:
                (idx, return_data, _s) = found
                self.reply(sock,return_data) # found[0][1] -->
                self.tuple_db['POST'].pop(idx)
            else:
                self.tuple_db['BLOCK'].append((sock,data))
            return

        if linda_cmd == 'IN_N':
            # Pull in, Non-blocking
            found = self.search_db('POST', data)
            print(found)
            if found:
                # (block_idx, return_data,s) = found
                (block_idx, return_data,_s) = found
                self.reply(sock,return_data)
                self.tuple_db['POST'].pop(post_idx)
            else:
                self.reply(sock,False)
            return

        if linda_cmd == 'RD_B':
            # Read, Blocking
            found = self.search_db('POST', data)
            if found:
                (block_idx, return_data, _s) = found
                # print('found; %s : %s' % (block_idx, return_data))
                self.reply(sock,return_data)
            else:
                self.tuple_db['BLOCK'].append((sock,data))
            return

        if linda_cmd == 'RD_N':
            # Read, Non-blocking
            found = self.search_db('POST', data)
            if found:
                (block_idx, return_data,_s) = found
                self.reply(sock,return_data)
            else:
                self.reply(sock,False)
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
                    print("|\t%s" %(str(record)[:100]))
            print("-\_" + '_'*50)
            '''
            for x in self.connections:
                addr, p = self.connections[x]
                print("|\t%s [%s]" % (p,addr))
            '''
            print("Connection=%s" % len(self.connections))
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
    server(PORT=port)
