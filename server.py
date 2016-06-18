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

"""------------------------------------------------------------*
    Declare
#------------------------------------------------------------"""
default_port = 21643
default_buff = 65536
max_buffer_len = 7

"""------------------------------------------------------------*
    Classes
#------------------------------------------------------------"""
class server(object):
    def __init__(self,PORT=default_port):
        self.recv_buffer = default_buff
        self.auto_port = int(PORT)
        self.auto_addr = ("0.0.0.0", self.auto_port)
        self.host = socket.gethostname()
        self.local = socket.gethostbyname(self.host)
        self.debug = True
        self.tuple_db = {True:[], False:[]}
        self.connections = {}
        self.activate = True
        self.service()

    @property
    def now(self):
        return datetime.datetime.utcnow()

    def setup(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.server_socket.bind((self.local,slef.auto_port))
        self.server_socket.listen(10)

        self.auto_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.auto_socket.bind(self.auto_addr)

        self.connections[self.server_socket] = (self.now, self.host, 'server_socket')
        self.connections[self.auto_socket] = (self.now,self.host, 'auto_socket')

    def service(self):
        self.report()
        print 1
        while self.activate:
            print 2
            read_list, write_list, exe_list = select.select(self.connections.keys(),[],[])
            print 3
            for sock in read_list:
                print 4
                if sock == self.auto_socket:
                    (p,fd) = sock.recvfrom(self.recv_buffer)
                    self.sendto(str(self.auto_port),fd)
                elif sock == self.server_socket:
                    sockfd, addr = self.server_socket.accept()
                    self.connections[sockfd] = (self.now, addr, p)
                else:
                    try:
                        data = self.xrcv(sock)
                        self.command(data,sock)
                    except:
                        print( "client lost")
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

    def xmit(self,sock,msg):
        sock.send(msg)
        sock.recv(2)

    def xrcv(self,sock):
        data = sock.recv(self.recv_buffer)
        sock.send('ok')
        return data

    def shutdown(self):
        self.activate = False

    def match(self, query, database):
        m = [record for record in database if (query in record)]
        if len(m) > 0:
            return True, database.pop(database.index(m[0]))
        else:
            return False, None


    def reply(self,sock,term):
        self.xmit(sock,pickle.dumps(term))

    def command(self, pickle_data, sock):
        _ = Any(Any)
        dt = Any(datetime.datetime)

        query_flag, block_flag, erase_flag, data = pickle.loads(pickle_data)

        '''
        Q   B   E   CMD
        F   -   -   Post message to tuplesapce
        T   T   T   Pull message from tuplespace, and remove
        T   T   F   Read message from tuplespace, do not remove
        T   F   T   Take message from tuplespace, else return false
        T   F   F   Peek message if found, else return false
        '''
        if query == "shutdown":
            self.shutdown()
            return

        search = not(query) # inverse boolean

        if query_flag:
            if data in self.tuple_db[search]:
                #idx,msg = [(i,x) for i,x in enumerate(self.tuple_db[search]) if data == x][0]
                found = [x for x in self.tuple_db[search] if data == x][0]
                idx = self.tuple_db[search].index(found)
                msg = self.tuple_db[search][idx]

                if erase_flag:
                    self.tuple_db[search].pop[idx]
                self.reply(sock,msg)
            else:
                if block:
                    self.tuple_db[query_flag].append((sock,data))
                else:
                    self.reply(sock,False)

        else:   # not a query means post to tupelspace
            packet = (_,data)
            for qry in self.tuple_db[search]:
                if qry == packet:
                    idx = self.tuple_db[search].index(qry)
                    send,msg = self.tuple_db[search].pop(idx)
                    self.reply(send,data)
                    return
            self.tuple_db[query_flag].append(data)
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
            n, addr, p = self.connections[x]
            print("|\t%s [%s]" % (p,addr))
