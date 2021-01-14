import sys
import sysv_ipc
# import multiprocessing
import threading
import os
import signal
import time


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
    if value>0:  # Home wants to sell
        mutex.acquire()
        stock = stock + value
        mutex.release()
    elif value<0:  # Home wants to buy
        if stock > abs(value):
            mutex.acquire()
            stock = stock + value
            mutex.release()
        else:
            print("Plus de STOCK !")
            mqMarket.send(b"", type=0)
            sys.exit(1)

    mq.send(b"", type=pid)  # Send an ACK
    print("stock is ", str(stock))
    print("Ending thread:", threading.current_thread().name)

if __name__ == "__main__":
    print("Market PID = ", os.getpid())
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGILL, handler)
    signal.signal(signal.SIGPIPE, handler)
    price, stock, war, tension, carbon, crisis = 1, 100000, 0, 0, 0, 0
    price = 0.9*price + (0.2*war + 0.5*tension + 0.5*carbon + 0.5*crisis)  #random coeff
    lock = threading.Lock()

    mqMarket = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)


    mqHome = sysv_ipc.MessageQueue(keyHome, sysv_ipc.IPC_CREAT)


    while True:
        while True:
            try:
                msg, tp = mqMarket.receive(type = 1, block=False)
                print(msg)
                p = threading.Thread(target=changeStock, args=(mqMarket, msg, tp, lock))
                p.start()
                p.join()
                price = 0.9 * price + (0.2 * war + 0.5 * tension + 0.5 * carbon + 0.5 * crisis)  # random coeff
                print("The current price is ", str(price))
                break
            except sysv_ipc.BusyError:
                pass
                # print("What the hell")

                """
                mqMarket.remove()
                mqHome.remove()
                """