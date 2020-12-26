import random
import time
from collections import deque

from USocket import UnreliableSocket
from socket import timeout as TimeoutException
from threading import Timer

# size of sending window
WINDOW_SIZE = 50
# max times of retrans
MAX_RETRY = 5
# size of receiving window
RCV_BUFF_SIZE = 50
# parameter
a = 0.125
b = 0.25


def get_send_to(sendto, addr):
    def result(data):
        sendto(data, addr)

    return result


def get_base(bool_arr):
    cnt = 0
    for i in bool_arr:
        if not i:
            break
        cnt += 1
    return cnt


class RDTSocket(UnreliableSocket):
    """
    The functions with which you are to build your RDT.
    -   recvfrom(bufsize)->bytes, addr
    -   sendto(bytes, address)
    -   bind(address)
    You can set the mode of the socket.
    -   settimeout(timeout)
    -   setblocking(flag)
    By default, a socket is created in the blocking mode.
    https://docs.python.org/3/library/socket.html#socket-timeouts
    """

    def __init__(self, rate=None, debug=True):
        super().__init__(rate=rate)
        self._rate = rate
        self._send_to = None
        self._recv_from = None
        self.target_addr = None
        self.buffer_size = 16 + 448
        self.debug = debug
        self.timer_list = []
        self.rtt_list = []
        self.send_win = deque(maxlen=WINDOW_SIZE)
        # self.send_win.
        self.con_addr = None
        self.EstRTT = -1
        self.DevRTT = -1
        self.TimeoutInterval = 3
        self.loss_list = []
        self.send_list = []
        self.loss_rate = 0
        self.syn_timer_1 = None
        self.syn_timer_2 = None
        self.fin_timer = None
        self.r_ack_timer = None
        self.r_fin_timer = None
        #############################################################################
        #############################################################################

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def bind(self, address: (str, int)):
        super(RDTSocket, self).bind(address)

    def accept(self):
        """
        Accept a connection. The socket must be bound to an address and listening for
        connections. The return value is a pair (conn, address) where conn is a new
        socket object usable to send and receive data on the connection, and address
        is the address bound to the socket on the other end of the connection.
        This function should be blocking.
        """
        try:
            conn, addr = RDTSocket(self._rate), None
            data, addr = self.recvfrom(self.buffer_size)
            # print("accept addr",addr)
            self.setblocking(True)
            pkt = decode(data)
            if pkt.syn:
                reply = RDTPacket(True, False, True, 0, 0, 0, b'')
                self.sendto(reply.encode(), addr)
            data, addr = self.recvfrom(self.buffer_size)
            if decode(data).ack:
                conn.set_recv_from(self.recvfrom)
                conn.set_send_to(get_send_to(conn.sendto, addr))
                return conn, addr
        except BlockingIOError:
            pass
        #############################################################################                                                    #
        #############################################################################
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def connect(self, address: (str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################                                                    #
        #############################################################################
        self.con_addr = address
        pkt = RDTPacket(True, False, False, 0, 0, 0, b'')

        self.syn_timer_1 = Timer(self.TimeoutInterval, self.handle_timeout_s1, args=(pkt, address))
        self.syn_timer_1.start()
        self.sendto(pkt.encode(), address)
        data, addr = self.recvfrom(self.buffer_size)
        self.syn_timer_1.cancel()

        if decode(data).syn and decode(data).ack:
            pkt2 = RDTPacket(False, False, True, 0, 0, 0, b'')

            self.syn_timer_2 = Timer(self.TimeoutInterval, self.handle_timeout_s2, args=(pkt2, address))
            self.syn_timer_2.start()
            self.sendto(pkt2.encode(), address)
            self.set_send_to(get_send_to(self.sendto, addr))
            self.set_recv_from(self.recvfrom)
            self.syn_timer_2.cancel()

            print("connection succeed with", address)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def cal_delay(self):
        if self.loss_rate > 0.7:
            return 0.1
        elif self.loss_rate > 0.5:
            return 0.05
        elif self.loss_rate > 0.3:
            return 0.03
        elif self.loss_rate > 0.1:
            return 0.01
        else:
            return 0

    def get_pos(self, seq_num, cur_win):
        for i in range(len(cur_win)):
            if seq_num == cur_win[i].seq:
                return i
        return -1

    def handle_timeout(self, pkt, acked):
        print("Time out pkt")
        print("Resend pkt #", pkt.seq)

        if acked[pkt.seq] == True:
            return

        self.loss_list.append(time.time())
        try:
            while True:
                if time.time() - self.loss_list[0] > 10:
                    self.loss_list.pop(0)
                else:
                    break
            while True:
                if time.time() - self.send_list[0] > 10:
                    self.send_list.pop(0)
                else:
                    break
        except:
            pass

        if len(self.loss_list) < len(self.send_list):
            self.loss_rate = len(self.loss_list) / len(self.send_list)
        print(len(self.loss_list), len(self.send_list), "loss_rate:", self.loss_rate)

        time.sleep(self.cal_delay())

        timer = Timer(self.TimeoutInterval, self.handle_timeout, args=(pkt, acked,))
        # print("pos:",self.get_pos(pkt.seq, self.send_win))
        try:
            self.timer_list[self.get_pos(pkt.seq, self.send_win)] = timer
            self.rtt_list[self.get_pos(pkt.seq, self.send_win)] = time.time()
        except:
            return
        self.send_list.append(time.time())
        self._send_to(pkt.encode())
        timer.start()

    def handle_timeout_s1(self, pkt, address):
        print("Time out pkt")
        print("Resend connect")

        self.syn_timer_1 = Timer(self.TimeoutInterval, self.handle_timeout_s1, args=(pkt, address))
        # print("pos:",self.get_pos(pkt.seq, self.send_win))
        self.sendto(pkt.encode(), address)
        self.syn_timer_1.start()

    def handle_timeout_s2(self, pkt, address):
        print("Time out pkt")
        print("Resend connect")

        self.syn_timer_2 = Timer(self.TimeoutInterval, self.handle_timeout_s2, args=(pkt, address))
        # print("pos:",self.get_pos(pkt.seq, self.send_win))
        self.sendto(pkt.encode(), address)
        self.syn_timer_2.start()

    def handle_timeout_v2(self, pkt):
        print("Time out pkt")
        print("Resend disconnect")

        self.fin_timer = Timer(self.TimeoutInterval, self.handle_timeout_v2, args=(pkt,))
        # print("pos:",self.get_pos(pkt.seq, self.send_win))
        self._send_to(pkt.encode())
        self.fin_timer.start()

    def handle_timeout_r1(self, pkt):
        self.r_ack_timer = Timer(self.TimeoutInterval, self.handle_timeout_r1, args=(pkt,))
        self._send_to(pkt.encode())
        self.r_ack_timer.start()

    def handle_timeout_r2(self, pkt):
        self.r_fin_timer = Timer(self.TimeoutInterval, self.handle_timeout_r2, args=(pkt,))
        self._send_to(pkt.encode())
        self.r_fin_timer.start()

    def recv(self, bufsize: int) -> bytes:
        """
        Receive data from the socket.
        The return value is a bytes object representing the data received.
        The maximum amount of data to be received at once is specified by bufsize.

        Note that ONLY data send by the peer should be accepted.
        In other words, if someone else sends data to you from another address,
        it MUST NOT affect the data returned by this function.
        """
        # Used to test send(), just send ack when receive packet
        # self.settimeout(1)
        # result = b''
        # cnt = 0
        # while True:
        #     try:
        #         data = self._recv_from(1000)
        #         p = decode(data[0])
        #         ack = RDTPacket(False, False, False, 0, p.seq, 0, b'')
        #         print("rev #", p.seq)
        #         if cnt == 0 and p.seq == 2:
        #             cnt += 1
        #             print("skip")
        #             continue
        #         self._send_to(ack.encode())
        #     except TimeoutException:
        #         print("Resend")

        # receive buffer
        buffer = deque(maxlen=RCV_BUFF_SIZE)
        # receive result
        result = b''

        # the needed seq of the data
        need = 0
        # the ack of received data
        ack = -1

        while True:
            try:
                # data = (packet, addr)
                data = self._recv_from(bufsize)
                pkt_rcv = decode(data[0])
                # End with four-way handshake
                if pkt_rcv.fin:
                    ack_pkt = RDTPacket(False, False, True, 0, 0, 0, b'')
                    self._send_to(ack_pkt.encode())
                    # self.r_ack_timer = Timer(self.TimeoutInterval, self.handle_timeout_r1, args=(ack_pkt,))
                    # self.r_ack_timer.start()

                    fin_pkt = RDTPacket(False, True, False, 0, 0, 0, b'')
                    self._send_to(fin_pkt.encode())
                    self.r_fin_timer = Timer(self.TimeoutInterval, self.handle_timeout_r2, args=(fin_pkt,))
                    self.r_fin_timer.start()

                    f_ack = self._recv_from(bufsize)
                    # self.r_ack_timer.cancel()
                    self.r_fin_timer.cancel()

                    if decode(f_ack[0]).ack:
                        break

                # Receive the packet
                ack = pkt_rcv.seq

                # print("buffer length:", len(buffer))
                if ack == need:
                    need += 1
                    # if len(buffer) != 0:
                    #     print("buffer[0]:", buffer[0].seq)
                    # print("need:", need)
                    result += pkt_rcv.payload
                    # clean the buffer
                    while len(buffer) != 0 and buffer[0].seq == need:
                        p = buffer.popleft()
                        result += p.payload
                        need += 1
                elif ack > need:
                    # If not full, add to the buffer
                    if len(buffer) == RCV_BUFF_SIZE:
                        continue
                    else:
                        inserted = False
                        for i in range(len(buffer)):
                            if pkt_rcv.seq == buffer[i].seq:
                                inserted = True
                        for i in range(len(buffer)):
                            if inserted:
                                break
                            if pkt_rcv.seq < buffer[i].seq:
                                buffer.insert(i, pkt_rcv)
                                inserted = True
                                break
                        if not inserted:
                            buffer.append(pkt_rcv)
                else:
                    pass
                print("ack #", ack)
                self._send_to(RDTPacket(False, False, False, 0, ack, 0, b'').encode())
            except TimeoutException:
                self._send_to(RDTPacket(False, False, False, 0, ack, 0, b'').encode())
            except ValueError:
                pass
        # print('recv buffer length', len(buffer))
        #############################################################################                                                     #
        #############################################################################

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return result

    def send(self, bytes: bytes):
        """
        Send data to the socket.
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """
        # TODO: Add max retry
        pkt_list = []
        # Split the data and get the whole packet list
        seq = 0
        while len(bytes) > self.buffer_size - 16:
            data = bytes[:self.buffer_size - 16]
            pkt = RDTPacket(False, False, False, seq, 0, self.buffer_size - 16, data)
            pkt_list.append(pkt)
            bytes = bytes[self.buffer_size - 16:]
            seq += 1
        if len(bytes) != 0:
            pkt_list.append(RDTPacket(False, False, False, seq, 0, len(bytes), bytes))
        acked = [False for _ in range(len(pkt_list))]
        # print(data_list)
        # Add packets to the window
        added = -1
        real_win_size = 0
        if len(pkt_list) > WINDOW_SIZE:
            real_win_size = WINDOW_SIZE
            for i in range(WINDOW_SIZE):
                self.send_win.append(pkt_list[i])
                added = i
        else:
            for i in pkt_list:
                real_win_size += 1
                self.send_win.append(i)

        sent = [False for _ in range(len(pkt_list))]
        # Send all packet in the window now
        window_base = 0
        for pkt in self.send_win:
            print("Send pkt #", pkt.seq)
            sent[pkt.seq] = True
            timer = Timer(self.TimeoutInterval, self.handle_timeout, args=(pkt, acked,))
            self.timer_list.append(timer)
            self.rtt_list.append(time.time())
            self._send_to(pkt.encode())
            self.send_list.append(time.time())
            timer.start()
        # Wait for acks
        retry = 0
        cnt1 = 0

        while True:
            try:
                # print("loop:", cnt1)
                # print("win_length", len(self.send_win))
                # print("window_base", window_base)
                cnt1 += 1
                data_rcv = self._recv_from(1000)
                p = decode(data_rcv[0])

                acked[p.seq_ack] = True
                win_pos = p.seq_ack - window_base
                # print("win_pos: ", win_pos)
                if win_pos >= 0:
                    self.timer_list[win_pos].cancel()
                    if self.EstRTT != -1:
                        self.EstRTT = (1 - a) * self.EstRTT + a * (time.time() - self.rtt_list[win_pos])
                    else:
                        self.EstRTT = time.time() - self.rtt_list[win_pos]
                    if self.DevRTT != -1:
                        self.DevRTT = (1 - b) * self.DevRTT + b * abs(
                            self.EstRTT - (time.time() - self.rtt_list[win_pos]))
                    else:
                        self.DevRTT = abs(self.EstRTT - (time.time() - self.rtt_list[win_pos]))
                    self.TimeoutInterval = 1.5 * self.EstRTT + 4 * self.DevRTT
                    self.TimeoutInterval += self.cal_delay()
                    # print("est_rtt: ", self.EstRTT)
                    # print("dev_rtt", self.DevRTT)
                    # print("self.Timeout:",self.TimeoutInterval)

                all_sent = True
                for i in sent:
                    if not i:
                        all_sent = False
                        break
                if all_sent:
                    all_acked = True
                    for i in acked:
                        if not i:
                            all_acked = False
                            break
                    if all_acked:
                        break
                    else:
                        continue
                retry = 0
                # record the ack and move the window
                window_base = get_base(acked)
                while len(self.send_win) != 0 and window_base > self.send_win[0].seq:
                    # print("win[0] =", self.send_win[0].seq)
                    # print("window_base", window_base)
                    self.send_win.popleft()
                    self.timer_list.pop(0)
                    self.rtt_list.pop(0)

                if len(self.send_win) == real_win_size:
                    continue
                add_num = 0
                if len(self.send_win) != 0:
                    add_num = WINDOW_SIZE - (self.send_win[-1].seq - window_base + 1)
                tmp_add = added + 1
                for i in range(add_num):
                    to_add = tmp_add + i  # to_add = added + 1 + i
                    if to_add < len(pkt_list):
                        timer = Timer(self.TimeoutInterval, self.handle_timeout, args=(pkt_list[to_add], acked,))
                        self.timer_list.append(timer)
                        self.rtt_list.append(time.time())
                        self._send_to(pkt_list[to_add].encode())
                        time.sleep(self.cal_delay())
                        self.send_list.append(time.time())
                        timer.start()
                        print("Send pkt #", pkt_list[to_add].seq)
                        self.send_win.append(pkt_list[to_add])
                        added = to_add
                    else:
                        break

                if len(self.send_win) == 0:
                    if added == len(pkt_list) - 1:
                        break
                    else:
                        p_to_send = pkt_list[added + 1]
                        timer = Timer(self.TimeoutInterval, self.handle_timeout, args=(p_to_send, acked,))
                        self.timer_list.append(timer)
                        self.rtt_list.append(time.time())
                        self.send_win.append(p_to_send)
                        self._send_to(p_to_send.encode())
                        time.sleep(self.cal_delay())
                        self.send_list.append(time.time())
                        timer.start()
                        added = added + 1

            except TimeoutException:
                # Retransmit the timeout packet
                retry += 1
                if retry >= MAX_RETRY:
                    print("connection failed")
                    break
            except ValueError:
                # ignore the packet if the packet corrupt
                pass
            except IndexError:
                print("Index Error")
                print("loop", cnt1)
                print("window base", window_base)
        self.send_fin()
        # self.close()
        # self.connect(self.con_addr)

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def send_fin(self):
        for t in self.timer_list:
            t.cancel()
        # End with four-way handshake
        fin_pkt = RDTPacket(False, True, False, 0, 0, 0, b'')
        self.fin_timer = Timer(self.TimeoutInterval, self.handle_timeout_v2, args=(fin_pkt,))
        self._send_to(fin_pkt.encode())
        self.fin_timer.start()
        retry = 0
        while True:
            try:
                data_rcv = self._recv_from(1000)
                if decode(data_rcv[0]).ack:
                    self.fin_timer.cancel()
                    break
            except TimeoutException:
                retry += 1
                if retry >= MAX_RETRY:
                    print("connection break")
                self._send_to(fin_pkt.encode())

        fin_rcv = self._recv_from(1000)
        if decode(fin_rcv[0]).fin:
            self._send_to(RDTPacket(False, False, True, 0, 0, 0, b'').encode())
        print("send end")

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither futher sends nor receives are allowed.
        """
        #############################################################################
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        super().close()

    def set_send_to(self, send_to):
        self._send_to = send_to

    def set_recv_from(self, recv_from):
        self._recv_from = recv_from


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.
"""


def get_separate(num):
    left = num >> 16
    return left, num - (left << 16)


def get_sum(data):
    result = 0
    if len(data) % 2 != 0:
        data = data + b'\x00'

    while len(data) != 0:
        cur = data[0:2]
        result += int.from_bytes(cur, 'big')
        data = data[2:]
    return result


class RDTPacket:
    """
    Form(in byte):
    1, 2: syn + fin + ack +00000
    3, 4, 5, 6: sequence number
    7, 8, 9, 10: sequence ack
    11, 12, 13, 14: length of payload
    15, 16: checksum
    17- : data
    """

    def __init__(self, syn: bool, fin: bool, ack: bool, seq: int, seq_ack: int, length: int, payload: bytes, check=0):
        self.syn = syn
        self.fin = fin
        self.ack = ack
        self.seq = seq
        self.seq_ack = seq_ack
        self.length = length
        self.payload = payload
        self.check = check

    def encode(self):
        result, check_sum = self.calculate()
        # check whether the packet is receiving or sending
        if self.check != 0:
            check_sum = hex(self.check)[2:]
        else:
            self.check = int(check_sum, 16)
        hex_str = check_sum
        if len(hex_str) == 3:
            hex_str = '0' + hex_str
        elif len(hex_str) == 2:
            hex_str = '00' + hex_str
        elif len(hex_str) == 1:
            hex_str = '000' + hex_str
        result += bytes.fromhex(hex_str)
        result += self.payload
        return result

    def calculate(self):
        head = 0x0000
        if self.syn:
            head |= 0x8000
        if self.fin:
            head |= 0x4000
        if self.ack:
            head |= 0x2000
        result = head.to_bytes(2, byteorder="big")
        seq1, seq2 = get_separate(self.seq)
        result += (seq1.to_bytes(2, "big") + seq2.to_bytes(2, "big"))
        seq_ack1, seq_ack2 = get_separate(self.seq_ack)
        result += (seq_ack1.to_bytes(2, "big") + seq_ack2.to_bytes(2, "big"))
        len1, len2 = get_separate(self.length)
        result += (len1.to_bytes(2, "big") + len2.to_bytes(2, "big"))
        check_sum = head + seq1 + seq2 + seq_ack1 + seq_ack2 + len1 + len2 + get_sum(self.payload)
        check_sum += self.check
        hex_chk_sum = hex(check_sum)[2:]
        overflow = 0
        if len(hex_chk_sum) > 4:
            overflow = int(hex_chk_sum[:len(hex_chk_sum) - 4], 16)
        check_sum += overflow
        if overflow == 0:
            check_sum = hex(check_sum)[2:]
        else:
            check_sum = hex(check_sum)[-4:]
        return result, hex(~int(check_sum, 16) & 0xFFFF)[2:]


def decode(packet) -> RDTPacket:
    # print(packet)
    info = packet[0:1]
    flag = bin(info[0] >> 5)[2:]
    syn, fin, ack = False, False, False
    if len(flag) == 1:
        flag = '00' + flag
    if len(flag) == 2:
        flag = '0' + flag
    if flag[0] == '1':
        syn = True
    if flag[1] == '1':
        fin = True
    if flag[2] == '1':
        ack = True
    seq = int.from_bytes(packet[2:6], 'big')
    seq_ack = int.from_bytes(packet[6:10], 'big')
    length = int.from_bytes(packet[10:14], 'big')
    second = hex(packet[15])[2:]
    if len(second) == 1:
        second = '0' + second
    check_sum = hex(packet[14])[2:] + second
    payload = packet[16:]
    result = RDTPacket(syn, fin, ack, seq, seq_ack, length, payload, check=int(check_sum, 16))
    try:
        r, chk = result.calculate()
        assert chk == '0'
        return result
    except AssertionError as e:
        print("check_sum", check_sum)
        print("calculated:", chk)
        print("Corrupted packet")
        raise ValueError from e