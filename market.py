import sys
import sysv_ipc
#import multiprocessing
import threading

key = 999
keyHome = 777

def changeStock(mq, msg, pid, mutex):
    print("Starting thread:", threading.current_thread().name)
    global stock
    msg = msg.decode()
    type, value = (int)(msg.split(","))
    if type == 1:  # Home wants to sell
        mutex.acquire()
        stock = stock + value
        mutex.release()
    elif type == 2:  # Home wants to buy
        # if stock < value: wait()
        mutex.acquire()
        stock = stock - value
        mutex.release()
    mq.send(b"", type=pid)  # Send an ACK
    print("Ending thread:", threading.current_thread().name)

if __name__ == "__main__":
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
