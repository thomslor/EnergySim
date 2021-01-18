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


def weather(mutex, temp):  # Process weather
    print("Weather PID ", os.getpid())
    while True:
        time.sleep(2)
        mutex.acquire()
        temp.value = temp.value + random.gauss(0, 4)
        mutex.release()
        # print("WEATHER: Temperature is ", temp.value)


def politics():  # Process politics: send randomly signals (SIGUSR1 & SIGUSR2) to market
    print("Politics PID ", os.getpid())
    pid = int(os.getppid())
    while True:
        time.sleep(10)
        random.randrange(0, 100)
        if random.randrange(0, 100) <= 20:
            print("*****WAR*****")
            os.kill(pid, signal.SIGUSR2)
        elif 20 < random.randrange(0, 100) <= 50:
            print("*****TENSION******")
            os.kill(pid, signal.SIGUSR1)


def economics():  # Process economics: send randomly signals (SIGILL & SIGPIPE) to market
    print("Economics PID ", os.getpid())
    pid = int(os.getppid())
    while True:
        time.sleep(10)
        ca, cr = random.randrange(0, 100), random.randrange(0, 100)
        if ca <= 30:
            print("*****CARBON*****")
            os.kill(pid, signal.SIGILL)
        if cr <= 30:
            print("*****CRISIS*****")
            os.kill(pid, signal.SIGPIPE)


def handler(sig, frame):  # Handle signals and modify values regarding the signal received
    global war, tension, carbon, crisis, stop, lockPol, lockCarbon, lockCrisis, mqMarket
    if sig == signal.SIGUSR2:
        lockPol.acquire()
        war = (war+1) % 2
        tension = 0
        lockPol.release()
    elif sig == signal.SIGUSR1:
        lockPol.acquire()
        tension = (tension+1) % 2
        lockPol.release()
    if sig == signal.SIGILL:
        lockCarbon.acquire()
        carbon = (carbon+1) % 2
        lockCarbon.release()
    if sig == signal.SIGPIPE:
        lockCrisis.acquire()
        crisis = (crisis+1) % 2
        lockCrisis.release()
    if sig == signal.SIGINT:  # Use to proper stop the program when receiving control-C or SIGINT
        mqMarket.send(b"", type=2)
        print("Home.py is ending")
        print(mqMarket.receive(type=3))
        stop = True


def changeStock(mq, msg, mutex):  # Change the stock according to the homes
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
        mutex.acquire()
        stock = stock + value
        mutex.release()
    mq.send(b"", type=pid)  # Send an ACK
    print("stock is ", str(stock))
    print("Ending thread:", threading.current_thread().name)


if __name__ == "__main__":
    marketPid = os.getpid()
    print("Market PID = ", marketPid)

    # Redirection of signals received
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGILL, handler)
    signal.signal(signal.SIGPIPE, handler)
    signal.signal(signal.SIGINT, handler)

    # Variables
    temperature = 15
    weatherTemp = multiprocessing.Value('d', temperature)
    price, stock, war, tension, carbon, crisis, overconsumption, stop = 1, 100000, 0, 0, 0, 0, 0, False

    # Locks
    lock = threading.Lock()
    lockWeather = threading.Lock()
    lockPol = threading.Lock()
    lockCrisis = threading.Lock()
    lockCarbon = threading.Lock()

    # Child processes
    pro = multiprocessing.Process(target=weather, args=(lockWeather, weatherTemp))
    politic = multiprocessing.Process(target=politics)
    economic = multiprocessing.Process(target=economics)
    pro.start()
    politic.start()
    economic.start()

    # Message queues
    mqMarket = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)
    mqHome = sysv_ipc.MessageQueue(keyHome, sysv_ipc.IPC_CREAT)

    while True:
        while True:  # Check if messages have been received in the market message queue
            try:
                message, _ = mqMarket.receive(type=1, block=False)
                # print(message)
                p = threading.Thread(target=changeStock, args=(mqMarket, message, lock))
                p.start()
                p.join()
                break
            except sysv_ipc.BusyError:
                pass
                # print("What the hell")
        lockPol.acquire()
        lockCarbon.acquire()
        lockCrisis.acquire()
        lockWeather.acquire()
        # print("Here    Here")
        price = 0.9 * price + temperature*(-0.5) + (0.2 * war + 0.7 * tension + 1.2 * carbon + 1.7 * crisis)
        lockWeather.release()
        lockPol.release()
        lockCarbon.release()
        lockCrisis.release()
        # print("The current price is ", str(price))
        # print("The temperature is ", weatherTemp.value)
        # print("Stop is ", stop)
        if stop:
            break

    # Proper end of the program when receiving control-C or SIGINT
    print("End")
    os.kill(pro.pid, signal.SIGTERM)
    os.kill(politic.pid, signal.SIGTERM)
    os.kill(economic.pid, signal.SIGTERM)
    """
    mqHome.remove()
    mqMarket.remove()
"""
