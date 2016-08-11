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
        # self.server_port = 1309
        # self.server_addr = ("0.0.0.0", self.server_port)
        self.auto_addr = ("0.0.0.0", self.auto_port)
        self.host = socket.gethostname()
        self.local = socket.gethostbyname(self.host)
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

        #self.server_socket.bind((self.host,self.auto_port))    # use the hostname :(
        self.server_socket.bind((self.local,self.auto_port))    # use the ip address :)
        # self.server_socket.listen(socket.SOMAXCONN)   # might be important, but it appears the clients are connecting fine.
        self.server_socket.listen(5)   # might be important, but it appears the clients are connecting fine.

        self.auto_socket = socket.socket(socket.AF_INET, # internet
                                            socket.SOCK_DGRAM) # UDP # socket.SOCK_STREAM) # TCP :
        print('auto addr', self.auto_addr)
        self.auto_socket.bind(self.auto_addr)

        self.connections[self.server_socket] = (self.host, 'server_socket')
        self.connections[self.auto_socket] = (self.host, 'auto_socket')

    def service(self):
        while self.activate:
            read_list, write_list, exe_list = select.select(self.connections.keys(),[],[])
            # self.report()
            for sock in read_list:

                # print(1)
                if sock == self.auto_socket:    #broadcast socket

                    (process_name,fd) = sock.recvfrom(self.recv_buffer)
                    # print(2, process_name)
                    sock.sendto(self.host,fd)
                elif sock == self.server_socket:    # connection request

                    client, addr = self.server_socket.accept()
                    # print(3, addr)
                    self.connections[client] = (addr, process_name)
                    #self.connections[client] = addr   # the process_name isn't going to be accurate, addr isn't used :(
                else: #if sock:
                    # print(4,sock)
                    try:
                        data = self.recv(sock)  # recieve method!
                        # print(pickle.loads(data))
                        if data:
                            self.command(data,sock)
                        # print('xyz')
                    except Exception as msg:
                    #except Exception as exception:
                        print( "Socket Error: %s" % msg)
                        print( pickle.loads(data) )
                        [self.tuple_db['BLOCK'].pop(self.tuple_db['BLOCK'].index(x)) for x in self.tuple_db['BLOCK'] if x[1] == sock]
                        for qry in self.tuple_db['BLOCK']:
                            idx = self.tuple_db['BLOCK'].index(qry)
                            if sock in qry:
                                self.tuple_db['BLOCK'].pop(idx)
                        del self.connections[sock]
                        sock.close()
                self.report()

        # shutdown server
        for x in self.connections:
            if x == self.server_socket:
                continue
            self.server_socket.close()


    def reply(self,sock,term):
        sock.send(pickle.dumps(term))      # TCP or UDP?

    def recv(self,sock):
        return sock.recv(default_buff)     # TCP or UDP?

    def shutdown(self):
        self.activate = False

    def match(self, query, database):
        m = [record for record in database if (query in record)]
        if len(m) > 0:
            return True, database.pop(database.index(m[0]))
        else:
            return False, None

    def search_db(self, db_name, match):
        if match in self.tuple_db[db_name]:
            return [(self.tuple_db[db_name].index(x),x) for x in self.tuple_db[db_name] if match == x] # [(idx,msg),]

    def command(self, pickle_data, sock):
        '''
        (data, linda_cmd)
        POST
        IN_B    (blocking)
        IN_N    (non-blocking)
        RD_B
        RD_N
        '''
        (data, linda_cmd) = pickle.loads(pickle_data)
        if linda_cmd == "shutdown":
            print('shutdown')
            self.shutdown()
            return

        if linda_cmd == 'POST':
            found = self.search_db('BLOCK',data)
            if found:
                block_idx, return_data = found[0]
                send, msg = self.tuple_db['BLOCK'].pop(block_idx) # found[0][0] --> index
                self.reply(send,data)
            else:
                self.tuple_db['POST'].append(data)
            return

        if linda_cmd == 'IN_B':
            # Pull in, Blocking
            found = self.search_db('POST', data)
            post_idx, return_data = found[0]
            if found:
                self.reply(return_data) # found[0][1] -->
                self.tuple_db['POST'].pop(post_idx)
            else:
                self.tuple_db['BLOCK'].append((sock,data))
            return

        if linda_cmd == 'IN_N':
            # Pull in, Non-blocking
            found = self.search_db('POST', data)
            post_idx, return_data = found[0]
            if found:
                self.reply(return_data)
                self.tuple_db['POST'].pop(post_idx)
            else:
                self.reply(sock,False)
            return

        if linda_cmd == 'RD_B':
            # Read, Blocking
            found = self.search_db('POST', data)
            post_idx, return_data = found[0]
            if found:
                self.reply(return_data)
            else:
                self.tuple_db['BLOCK'].append((sock,data))
            return

        if linda_cmd == 'RD_N':
            # Read, Non-blocking
            found = self.search_db('POST', data)
            if found:
                post_idx, return_data = found[0]
                print(return_data)
                self.reply(return_data)
            else:
                self.reply(sock,False)
            return
        self.report()

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
            for x in self.connections:
                addr, p = self.connections[x]
                print("|\t%s [%s]" % (p,addr))
        print(len(self.connections))
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
