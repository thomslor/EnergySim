import sys
import sysv_ipc
# import multiprocessing
import threading
import os
import signal


key = 999
keyHome = 777

def handler(sig, frame):
    global war, tension, carbon, crisis
    if sig == signal.SIGUSR2:
        war = (war+1) % 2
        tension = 0
    elif sig == signal.SIGUSR1:
        tension = (tension+1) % 2
    if sig == signal.SIGILL:
        carbon = (carbon+1) % 2
    if sig == signal.SIGPIPE:
        crisis = (crisis+1) % 2

def changeStock(mq, msg, tp, mutex):
    print("Starting thread:", threading.current_thread().name)
    global stock
    msg = msg.decode()
    print("msg is ", msg)
    pid, value = msg.split(",")
    pid, value = int(pid), int(value)
    if tp == 1:  # Home wants to sell
        mutex.acquire()
        stock = stock + value
        mutex.release()
    elif tp == 2:  # Home wants to buy
        # if stock < value: wait()
        mutex.acquire()
        stock = stock - value
        mutex.release()
    mq.send(b"", type=pid)  # Send an ACK
    print("stock is ", str(stock))
    print("Ending thread:", threading.current_thread().name)

if __name__ == "__main__":
    print("Market PID = ", os.getpid())
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGILL, handler)
    signal.signal(signal.SIGPIPE, handler)
    price, stock, war, tension, carbon, crisis = 1, 0, 0, 0, 0, 0
    price = 0.9*price + (0.2*war + 0.5*tension + 0.5*carbon + 0.5*crisis)  #random coeff
    lock = threading.Lock()

    try:
        mqMarket = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
    except ExistentialError:
        print("Message queue", key, "already exist, terminating.")
        sys.exit(1)

    try:
        mqHome = sysv_ipc.MessageQueue(keyHome, sysv_ipc.IPC_CREX)
    except ExistentialError:
        print("Message queue", keyHome, "already exist, terminating.")
        sys.exit(1)

    while True:
        msg, pid = mqMarket.receive()
        p = threading.Thread(target=changeStock, args=(mqMarket, msg, pid, lock))
        p.start()
        p.join()
        mqMarket.remove()
        mqHome.remove()
        break
