import sys
import sysv_ipc
#import multiprocessing
import threading

key = 999

def worker(msg, tp, mutex):
    print("Starting thread:", threading.current_thread().name)
    global stock
    if tp ==
    mutex.acquire()

    mutex.release()
    message = str(dt).encode()
    pid = int(msg.decode())
    t = pid + 3
    mq.send(message, type=t)
    print("Ending thread:", threading.current_thread().name)

if __name__ == "__main__":
    price, stock, war, tension, carbon, crisis = 1, 0, 0, 0, 0, 0
    price = 0.9*price + (0.2*war + 0.5*tension + 0.5*carbon + 0.5*crisis)  #random coeff
    lock = threading.Lock()
    try:
        mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
    except ExistentialError:
        print("Message queue", key, "already exsits, terminating.")
        sys.exit(1)

    threads = []
    while True:
        msg, tp = mq.receive()
        if tp == 1:
            p = threading.Thread(target=worker, args=(msg, tp, lock))
            p.start()
            threads.append(p)
        if tp == 2:
            for thread in threads:
                thread.join()
            mq.remove()
            break
