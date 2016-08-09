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
        self.server_socket.listen(socket.SOMAXCONN)   # might be important, but it appears the clients are connecting fine.

        self.auto_socket = socket.socket(socket.AF_INET, # internet
                                            socket.SOCK_DGRAM) # UDP # socket.SOCK_STREAM) # TCP : 
        print('auto addr', self.auto_addr)
        self.auto_socket.bind(self.auto_addr)

        self.connections[self.server_socket] = (self.host, 'server_socket')
        self.connections[self.auto_socket] = (self.host, 'auto_socket')

    def service(self):
        self.report()
        while self.activate:
            # print(self.connections.values())
            read_list, write_list, exe_list = select.select(self.connections.keys(),[],[])
            print(len(read_list), len(write_list), len(exe_list))   # are there write list entries?
            for sock in read_list:
                if sock == self.auto_socket:    #broadcast socket
                    (process_name,fd) = sock.recvfrom(self.recv_buffer)
                    sock.sendto(self.host,fd)
                elif sock == self.server_socket:    # connection request
                    client, addr = self.server_socket.accept()
                    #self.connections[client] = (addr, process_name)
                    self.connections[client] = addr   # the process_name isn't going to be accurate, addr isn't used :(
                else:
                    try:
                        data = self.recv(sock)  # recieve method!
                        self.command(data,sock)
                    except Exception as msg:
                    #except Exception as exception:
                        print( "Socket Error: %s" % msg)
                        [self.tuple_db[True].pop(self.tuple_db[True].index(x)) for x in self.tuple_db[True] if x[1] == sock]
                        for qry in self.tuple_db[True]:
                            idx = self.tuple_db[True].index(qry)
                            if sock in qry:
                                self.tuple_db[True].pop(idx)
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
        data_load = pickle.loads(pickle_data)
        ( data,
        query_flag,
        block_flag,
        erase_flag,
        multi_flag ) = data_load

        # print(data_load)

        '''
        Q   B   E   M   CMD
        F   -   -   ?   POST message to tuplesapce
        T   T   T   ?   PULL message from tuplespace, and remove
        T   T   F   ?   READ message from tuplespace, do not remove
        T   F   T   ?   PULL message from tuplespace, else return false
        T   F   F   ?   READ message if found, else return false
        
        (data, type, socket)
        POST
        IN_B    (blocking)
        IN_N    (non-blocking)
        RD_B
        RD_N
        '''
        if linda_cmd == "shutdown":
            print('shutdown')
            self.shutdown()
            return

        if linda_cmd == 'POST':
            found = self.search_db('BLOCK',data)
            if found:
                send, msg = self.tuple_db['BLOCK'].pop(found[0][0]) # found[0][0] --> index
                self.reply(send,data)
            else:
                self.tuple_db['POST'].append(data)
            return
        
        if linda_cmd == 'IN_B':
            # Pull in, Blocking
            found = self.search_db('POST', data)
            if found:
                self.reply(found[0][1]) # found[0][1] --> 
                self.tuple_db['POST'].pop(found[0][0])
            else:
                self.tuple_db['BLOCK'].append((sock,data))
            return

        if linda_cmd == 'IN_N':
            # Pull in, Non-blocking
            found = self.search_db('POST', data)
            if found:
                self.reply(found[0][1])
                self.tuple_db['POST'].pop(found[0][0])
            else:
                self.reply(sock,False)
            return

        if linda_cmd == 'RD_B':
            # Read, Blocking
            found = self.search_db('POST', data)
            if found:
                self.reply(found[0][1])
                return
            else:
                self.tuple_db['BLOCK'].append((sock,data))
            return
        
        if linda_cmd == 'RD_N':
            # Read, Non-blocking
            found = self.search_db('POST', data)
            if found:
                self.reply(found[0][1])
                
            else:
                self.reply(sock,False)
            return
        
            
        search = not(query_flag) # inverse boolean
        # print(search)
        if query_flag:
            tic = time.time()
            # print('query!')
            if data in self.tuple_db[search]:

                #idx,msg = [(i,x) for i,x in enumerate(self.tuple_db[search]) if data == x][0]
                found = [x for x in self.tuple_db[search] if data == x][0]
                print(found)
                idx = self.tuple_db[search].index(found)
                msg = self.tuple_db[search][idx]
                if erase_flag:
                    self.tuple_db[search].pop(idx)
                self.reply(sock,msg)
            else:
                # print(data)
                if block_flag:
                    self.tuple_db[query_flag].append((sock,data))
                else:
                    self.reply(sock,False)
                    x = time.time() - tic
        else:   # not a query means post to tupelspace
            # print('post!')
            packet = (_,data)
            for data in self.tuple_db[search]:
                if data == packet:
                    idx = self.tuple_db[search].index(data)
                    send,msg = self.tuple_db[search].pop(idx)
                    self.reply(send,data)
                    return
            self.tuple_db[query_flag].append(data)
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
