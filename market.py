import sys
import sysv_ipc
import multiprocessing
import threading
import os
import signal
import random
import time


key = 999
keyHome = 777


def weather(mutex, temp):
    while True:
        time.sleep(2)
        mutex.acquire()
        temp.value = temp.value + random.gauss(0, 4)
        mutex.release()
        print("WEATHER: Temperature is ", temp.value)


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


def changeStock(mq, msg, mutex):
    print("Starting thread:", threading.current_thread().name)
    global stock
    msg = msg.decode()
    print("msg is ", msg)
    pid, value = msg.split(",")
    pid, value = int(pid), int(value)
    if value > 0:  # Home wants to sell
        mutex.acquire()
        stock = stock + value
        mutex.release()
    elif value < 0:  # Home wants to buy
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
    temperature = 15
    weatherTemp = multiprocessing.Value('d', temperature)
    price, stock, war, tension, carbon, crisis, overconsumption = 1, 100000, 0, 0, 0, 0, 0
    lock = threading.Lock()
    lockWeather = threading.Lock()

    pro = multiprocessing.Process(target=weather, args=(lockWeather, weatherTemp))
    pro.start()

    mqMarket = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)
    mqHome = sysv_ipc.MessageQueue(keyHome, sysv_ipc.IPC_CREAT)

    while True:
        while True:
            try:
                msg, tp = mqMarket.receive(type=1, block=False)
                print(msg)
                p = threading.Thread(target=changeStock, args=(mqMarket, msg, lock))
                p.start()
                p.join()
                break
            except sysv_ipc.BusyError:
                pass
                # print("What the hell")
        lockWeather.acquire()
        print("Here    Here")
        price = 0.9 * price + temperature*(-0.5) + (0.2 * war + 0.7 * tension + 1.2 * carbon + 1.7 * crisis) # random coeff
        lockWeather.release()
        # print("The current price is ", str(price))
        print("The temperature is ", weatherTemp.value)

        """
                mqMarket.remove()
                mqHome.remove()
                """
    pro.join()