from socket import *
import time
import threading
import json
import pickle
import math
import time
import numpy as np
from multiprocessing import Process
import sys
import config

BUFSIZ = 1024

class node:

    def __init__(self, idx, seed=123):

        self.port_basis = 9000
        self.my_port = self.port_basis+idx

        self.if_start_up = True
        self.master = True
        self.timeslot = None
        self.master_ID = None
        self.F = None
        self.F_list = []
        self.master_ID_list = []
        self.timeslot_available = np.arange(1,8)
        self.timeslot_occupied = []
        self.children = []

        self.applying = []
        self.applying_pending = {}
        self.all_available = [1, 2, 3, 4, 5, 6, 7]
        # 读取拓扑，获取每个点的坐标
        self.x_list, self.y_list, self.node_num = self.get_topology()
        np.random.seed(seed)

        # 存储已经收到的报文，src——address
        self.received_src = []
        # 记录id，第几次路由
        self.idx=0

        recv_socket = socket(AF_INET, SOCK_DGRAM)
        print(('127.0.0.1', self.my_port))
        recv_socket.bind(('127.0.0.1', self.my_port))
        self.recv_socket = recv_socket


    # 向某个节点发送报文信息
    def send(self, msg, to_port):
        self.recv_socket.sendto(msg.encode('utf-8'), ('127.0.0.1', to_port))
        # print("---Send:","----Port:",str(to_port), msg)

    def broadcast(self, msg):
        # 查看拓扑
        self.x_list, self.y_list, self.node_num = self.get_topology()

        # 本节点的index
        index = self.my_port-self.port_basis-1

        for i in range(self.node_num):
            if i!=index:
                # 广播，距离N=5以内的节点均可以广播到
                if math.sqrt(math.pow((self.x_list[i]-self.x_list[index]),2)+
                             math.pow((self.y_list[i]-self.y_list[index]),2))<config.radius:
                    self.send(msg, i+self.port_basis+1)

    def get_topology(self):
        # 从文件读取拓扑
        pkl_file = open(config.y, 'rb')
        y_list = pickle.load(pkl_file)
        pkl_file.close()

        pkl_file = open(config.x, 'rb')
        x_list = pickle.load(pkl_file)
        pkl_file.close()
        # 端口数目
        node_num = len(x_list)
        # 根据端口数目设置所有端口
        self.allport = []
        for i in range(node_num):
            port_temp = i + 1 + self.port_basis
            self.allport.append(port_temp)
        return x_list, y_list, node_num

    def fast_send(self):
        print("Start Fast Sending .--------------")
        F = np.random.choice(config.all_F)
        self.F = F
        while True:
            time.sleep(0.2)
            print("fast_sending...")
            msg = write_json(des_address="", src_address=self.my_port, content=self.timeslot_available,
                             master_ID=self.my_port, F=F, F_list=self.F_list, flag="FAST_SEND")
            self.broadcast(msg)

    def broadcast_HELLO(self):
        print("Start broadcast HELLO in period")
        while True:
            time.sleep(1)
            msg = write_json(des_address="", src_address=self.my_port, content=self.timeslot_available,
                             master_ID=self.master_ID, F=self.F, F_list=self.F_list, flag="HELLO")
            if self.master:
                print("HELLO:本端%d为中心节点%d，子网中有：%s，占用时隙%s, 可用时隙%s" % (self.my_port,self.F, str(self.children),
                                                               str(self.timeslot_occupied), str(self.timeslot_available)))
            else:
                print("HELLO:本端%d，所在的子网%s，中心节点ID%s，占用时隙%s, 可用时隙%s"%(self.my_port, str(self.F_list),
                                                       str(self.master_ID_list), str(self.timeslot_occupied), str(self.timeslot_available)))
            self.broadcast(msg)


    def run(self):
        p_fast_send = Process(target=self.fast_send)
        p_HELLO = threading.Thread(target=self.broadcast_HELLO)
        while True:
            # 如果刚开机
            if self.if_start_up:
                self.if_start_up = False
                print("%d开机，开始持续5s的监听"%self.my_port)
                # 扫频慢收。5秒没有响应，则开始快发
                self.recv_socket.settimeout(5)
                try:
                    while True:
                        data, address = self.recv_socket.recvfrom(BUFSIZ)
                        des_address, src_address, content, master_ID, F, F_list, flag = parse_json(data.decode('utf-8'))

                        # 如果收到了”快发“或者心跳信息，向其所在的中心节点申请入网
                        # TODO 如果几乎同时收到了两个中心节点的消息，待处理
                        if flag == "FAST_SEND" or flag == "HELLO":
                            print("%dReceive %s from address %d" % (self.my_port, flag, src_address))
                            # 向master申请入网
                            msg = write_json(des_address=master_ID, src_address=self.my_port,
                                             content=[], master_ID="", F=F, F_list=self.F_list, flag="APPLY")
                            print("APPLY to master:", master_ID)
                            self.broadcast(msg)
                            # 等待中心节点的确认消息，如果收到ACK，入网成功。如果超时5s未收到ACK，独立建网
                            t1=time.time()
                            while True:
                                # 收到的msg一直都不是ACK，3秒还没有收到ACK消息，break
                                if time.time()-t1 > 3:
                                    recv_response = False
                                    break
                                data, address = self.recv_socket.recvfrom(BUFSIZ)
                                des_address, src_address, content, master_ID, F, F_list, flag = parse_json(
                                    data.decode('utf-8'))
                                if flag == "ACK" and des_address == self.my_port:
                                    print("Receive ACK from %d, connected to this master" % src_address)
                                    self.master = False
                                    self.timeslot = content
                                    self.timeslot_occupied.append(self.timeslot)
                                    self.timeslot_available = np.setdiff1d(self.all_available, self.timeslot_occupied)
                                    self.master_ID = master_ID
                                    self.master_ID_list.append(self.master_ID)
                                    self.F = F
# F_list的长度如果达到3，不再加入新的子网
                                    self.F_list.append(self.F)
                                    print(
                                        "%d连接至子网，时隙：%s，中心节点：%s，频率：%s" % (self.my_port, str(self.timeslot_occupied),
                                                                         str(self.master_ID_list),
                                                                         str(self.F_list)))
                                    recv_response = True


                                    self.recv_socket.settimeout(None)
                                    break

                            break
                except timeout:
                    print("没有监听到周围节点")
                    recv_response = False
                # 没有发现别的节点，成为中心节点，进行扫频快发
                if not recv_response:
                    print("开始持续20s的快发")
                    self.recv_socket.settimeout(40)
                    # 开启新进程，开始快发
                    p_fast_send.start()
                    # 20s没有人响应，则关机
                    try:
                        while True:
                            data, address = self.recv_socket.recvfrom(BUFSIZ)
                            des_address, src_address, content, master_ID, F, F_list, flag = parse_json(data.decode('utf-8'))

                            # 收到申请
                            if flag == "APPLY" and des_address == self.my_port:
                                print("%d Receive APPLY from %d"%(self.my_port,src_address))
                                # 结束快发
                                p_fast_send.terminate()
                                # 发送ACK，分配时隙，自己作为master
                                self.master = True
                                self.master_ID = self.my_port
                                self.master_ID_list.append(self.master_ID)

                                # 分配自己的时隙,更新可用时隙
                                self.timeslot = self.timeslot_available[0]
                                self.timeslot_occupied.append(self.timeslot)
                                self.timeslot_available = np.delete(self.timeslot_available,
                                                                    np.where(self.timeslot_available==self.timeslot))

# Change Here. 不考虑申请节点的时隙情况。总是以新的发送端发送入网申请。
                                # 分配申请入网节点的时隙,更新可用时隙
                                allocated_timeslot = self.timeslot_available[0]
                                self.timeslot_available = np.delete(self.timeslot_available,
                                                                    np.where(
                                                                        self.timeslot_available == allocated_timeslot))

                                # 发送ACK
                                to_port = src_address
                                self.children.append(to_port)
                                msg = write_json(des_address=to_port, src_address=self.my_port, F_list=self.F_list,
                                                 content=allocated_timeslot, master_ID=self.my_port, F=F, flag="ACK")
                                self.F = F
                                self.F_list.append(self.F)
                                print("send back ACK， %d入网成功 :"%to_port)
                                print("子网建成，本端为中心节点%d，时隙：%s，频率：%s，网内节点：%s" % (self.my_port, str(self.timeslot_occupied),
                                                                       str(self.F_list), str(self.children)))
                                self.broadcast(msg)



                                self.recv_socket.settimeout(None)
                                break
                            # TODO 两个节点几乎同时开机，没有监听到后，都在快发的特殊情况，需要考虑。
                            # if flag == "APPLY"   p_fast_send.terminate()

                    except timeout:
                        print("20秒内没有收到申请入网消息，关机")
                        p_fast_send.terminate()
                        self.recv_socket.close()
                        return 0

            # 开始广播HELLO心跳信息
            if not p_HELLO.is_alive():
                print("开始定时广播")
                p_HELLO.start()
            # 正常运行模式，持续扫频慢收监听
            data, address = self.recv_socket.recvfrom(BUFSIZ)
            des_address, src_address, content, master_ID, F, F_list, flag = parse_json(data.decode('utf-8'))
            # 中心节点在运行过程中收到刚开机节点的入网申请
            if self.master:
                # 收到申请入网消息
                if flag == "APPLY" and des_address == self.my_port:

# Change Here. 不考虑申请节点的时隙情况。
                    if len(self.timeslot_available) > 0:
                        print("%d Receive APPLY from %d"%(self.my_port,src_address))
                        to_port = src_address
                        # 分配时隙
                        # content不为空，即为申请节点的占有时隙，可用时隙中去掉这些时隙
                        allocated_timeslot = self.timeslot_available[0]

                        self.timeslot_available = np.delete(self.timeslot_available,
                                                            np.where(self.timeslot_available==allocated_timeslot))
                        self.children.append(to_port)
                        msg = write_json(des_address=to_port, src_address=self.my_port, F_list=self.F_list,
                                         content=allocated_timeslot, master_ID=self.my_port, F=self.F, flag="ACK")
                        self.broadcast(msg)
                        print("send back ACK， %d入网成功 :"%to_port)
                        print("本端%d为中心节点%d，目前子网内有%d个子节点:%s"%(self.my_port,
                                                             self.F, 7-self.timeslot_available.size-1, str(self.children)))

            # 如果某新开机节点a无法加入本子网，a进行快发，该节点在新的频率上收到了a的快发消息。则该节点向a申请入网
            if flag == "FAST_SEND" or flag == "HELLO":
# F_list的长度如果达到3，不再加入新的子网
                # 1)首先判断是否是子网内其他节点的消息。
                # 2)其次判断当前发送端是否占满了
                # 3)多次收到其他子网的消息，不再重复发APPLY入网申请
                # 4) DELETED，不再判断是否有可用时隙
                if np.intersect1d(F_list, self.F_list).size == 0 \
                    and len(self.F_list) < 3 \
                    and master_ID not in self.applying:

                    print("%d Receive %s from address %d" % (self.my_port, flag, src_address))
                    self.applying.append(master_ID)
# 阻塞，防止一次性申请进入多个子网，导致超过发送端口个数
                    self.F_list.append(F)

                    # 向master申请入网,content是自己已占有的时隙， master分配的时候排除这些时隙
                    msg = write_json(des_address=master_ID, src_address=self.my_port, F_list=self.F_list,
                                 content=self.timeslot_occupied, master_ID="", F=F, flag="APPLY")
                    print("APPLY to master:", master_ID)
                    self.broadcast(msg)

                    t_recv = time.time()
                    self.applying_pending[master_ID] = [t_recv, F]

            if len(self.applying_pending)>0:
                pending_appling = self.applying_pending.copy()
                tmp = pending_appling.popitem()
                pending_ID, pending_time_F = tmp[0], tmp[1]
                pending_time, pending_F = pending_time_F[0], pending_time_F[1]
                if time.time()-pending_time>4:
                    del self.applying_pending[pending_ID]
                    # 如果没有成功申请进入，释放该发送端口
                    self.F_list.remove(pending_F)

                    p_fast_send_running = Process(target=self.fast_send)
                    print("申请无响应，开始持续4s的快发")
                    # 开启新进程，开始快发
                    p_fast_send_running.start()

                    t_wait = time.time()
                    while True:
                        # 4s没有收到申请消息，回归原始状态
                        if time.time() - t_wait > 4:
                            print("4秒内没有收到邻近节点的申请入网消息，回归到原子网中，继续保持运行状态")
                            p_fast_send_running.terminate()
                            break
                        data, address = self.recv_socket.recvfrom(BUFSIZ)
                        des_address, src_address, content, master_ID, F, F_list, flag = parse_json(data.decode('utf-8'))
                        # 收到申请
                        if flag == "APPLY" and des_address == self.my_port:
                            print("%d Receive APPLY from %d"%(self.my_port,src_address))
                            # 结束快发
                            p_fast_send_running.terminate()
                            # 发送ACK，分配时隙，自己作为master
                            self.master = True
                            self.master_ID = self.my_port
                            self.master_ID_list.append(self.master_ID)

                            # 如果申请入网的节点已经在另外一个网内，排除掉其已占有的时隙
                            # content 是申请节点的所有占有时隙
                            applying_timeslot_occupied = content
                            applying_timeslot_available = np.setdiff1d(self.all_available,
                                                                       applying_timeslot_occupied).tolist()
                            timeslot_available = np.intersect1d(applying_timeslot_available,
                                                                self.timeslot_available).tolist()

                            # 分配申请入网节点的时隙,更新可用时隙
                            allocated_timeslot = timeslot_available[0]
                            self.timeslot_available = np.delete(self.timeslot_available,
                                                                np.where(self.timeslot_available == allocated_timeslot))
                            # 分配自己的时隙,更新可用时隙
                            self.timeslot = self.timeslot_available[0]
                            self.timeslot_occupied.append(self.timeslot)
                            self.timeslot_available = np.delete(self.timeslot_available,
                                                                np.where(self.timeslot_available == self.timeslot))
                            # 发送ACK
                            to_port = src_address
                            self.children.append(to_port)
                            msg = write_json(des_address=to_port, src_address=self.my_port, F_list=self.F_list,
                                             content=allocated_timeslot, master_ID=self.my_port, F=F, flag="ACK")
                            self.F = F
                            self.F_list.append(self.F)
                            print("send back ACK， %d入网成功 :" % to_port)
                            print("子网建成，本端为中心节点%d，时隙：%s，频率：%s，网内节点：%s" % (self.my_port, str(self.timeslot_occupied),
                                                                          str(self.F_list), str(self.children)))
                            self.broadcast(msg)
                            self.recv_socket.settimeout(None)
                            break


            # 收到了该节点在正常运行过程中申请入网之后的确认消息
            if flag == "ACK" and des_address == self.my_port:
                print("Receive ACK from %d, connected to this master" % src_address)
                if master_ID in self.applying:
                    self.applying.remove(master_ID)
                del self.applying_pending[master_ID]

                self.timeslot = content
                self.timeslot_occupied.append(self.timeslot)
                self.timeslot_available = np.setdiff1d(self.all_available, self.timeslot_occupied)
                self.master_ID = master_ID
                self.master_ID_list.append(self.master_ID)
                self.F = F
                print("%d连接至子网%d，时隙%s：，中心节点%s：，频率%s：" % (self.my_port, F, str(self.timeslot_occupied),
                                                       str(self.master_ID_list), str(self.F_list)))

        self.recv_socket.close()

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)
class redirect:
    content = ""

    def write(self,str):
        self.content += str

    def flush(self):
        self.content = ""
# 打包报文数据，形成json格式报文
def write_json(des_address, src_address, content, master_ID, F, F_list, flag):
    python2json = {}
    # route_list = [1, 2, 3]
    python2json["content"] = content
    python2json["src_address"] = src_address
    python2json["des_address"] = des_address
    python2json["flag"] = flag
    python2json["master_ID"] = master_ID
    python2json["F"] = F
    python2json["F_list"] = F_list
    json_str = json.dumps(python2json, cls=NpEncoder)
    return json_str

def parse_json(json_str):
    json2python = json.loads(json_str)
    return json2python['des_address'], json2python['src_address'], json2python['content'],\
           json2python['master_ID'], json2python['F'], json2python['F_list'], json2python['flag']

if __name__ == '__main__':
    c = node(4)
    c.run()