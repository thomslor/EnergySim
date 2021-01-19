import sysv_ipc
import multiprocessing
import threading
import os
import signal
import random
import time

# Keys of both messages queues
key = 999
keyHome = 777


def weather(mutex, temp):  # Process weather
    print("Weather PID: ", os.getpid())
    while True:
        time.sleep(random.randrange(2, 11, 1))
        mutex.acquire()
        temp.value = temp.value + random.gauss(0, 4)
        if temp.value >= 45:
            temp.value = 40
        elif temp.value <= -30:
            temp.value = -25
        mutex.release()



def politics():  # Process politics: send randomly signals (SIGUSR1 & SIGUSR2) to market
    print("Politics PID: ", os.getpid())
    pid = int(os.getppid())
    while True:
        time.sleep(10)
        random.randrange(0, 100)
        if random.randrange(0, 100) <= 10:
            os.kill(pid, signal.SIGUSR2)
        elif 20 < random.randrange(0, 100) <= 30:
            os.kill(pid, signal.SIGUSR1)


def economics():  # Process economics: send randomly signals (SIGILL & SIGPIPE) to market
    print("Economics PID: ", os.getpid(), "\n")
    pid = int(os.getppid())
    while True:
        time.sleep(10)
        ca, cr = random.randrange(0, 100), random.randrange(0, 100)
        if ca <= 20:
            os.kill(pid, signal.SIGILL)
        if cr <= 20:
            os.kill(pid, signal.SIGPIPE)


def handler(sig, frame):  # Handle signals and modify values regarding the signal received
    global war, tension, carbon, crisis, stop, mqMarket
    if sig == signal.SIGUSR2:
        printhandler("war")
        war = (war+1) % 2
        tension = 0
    elif sig == signal.SIGUSR1:
        printhandler("tension")
        tension = (tension+1) % 2
    if sig == signal.SIGILL:
        printhandler("carbon")
        carbon = (carbon+1) % 2
    if sig == signal.SIGPIPE:
        printhandler("crisis")
        crisis = (crisis+1) % 2
    if sig == signal.SIGINT:  # Use to proper stop the program when receiving control-C or SIGINT
        mqMarket.send(b"", type=2)
        printhandler("stop")
        mqMarket.receive(type=3)
        stop = True

def printhandler(signal):
    global war, tension, carbon, crisis, stop, mqMarket
    if signal == "war":
        if war == 0:
            print("*****WAR BEGINS*****")
            if tension == 1:
                print("*****AND ERASES TENSIONS*****")
        else:
            print("*****WAR ENDS*****")
    if signal == "tension":
        if tension == 0:
            print("*****DIPLOMATIC TENSIONS*****")
        else:
            print("*****NO MORE TENSIONS*****")
    if signal == "carbon":
        if carbon == 0:
            print("*****CARBON RAISES*****")
        else:
            print("*****CARBON DECREASES*****")
    if signal == "crisis":
        if crisis == 0:
            print("*****HUGE CRISIS*****")
        else:
            print("*****REGROWTH AFTER CRISIS*****")
    if signal == "stop":
        print("maison.py is ending...")


def changeStock(mq, msg, mutex):  # Change the stock according to the homes
    global stockvar
    msg = msg.decode()
    pid, value = msg.split(",")
    pid, value = int(pid), int(value)
    if value > 0:  # Home wants to sell
        mutex.acquire()
        stockvar += value
        mutex.release()
        typeTransaction = "Sales"
    elif value < 0:  # Home wants to buy
        mutex.acquire()
        stockvar += value
        mutex.release()
        typeTransaction = "Purchase"
    mq.send(b"", type=pid)  # Send an ACK
    # print("Transaction with Home ", pid, ", ", typeTransaction, ", stock is now :", str(stock))



if __name__ == "__main__":
    marketPid = os.getpid()
    print("Market PID: ", marketPid)

    # Redirection of signals received
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGILL, handler)
    signal.signal(signal.SIGPIPE, handler)
    signal.signal(signal.SIGINT, handler)

    # Variables
    temperature = 15
    weatherTemp = multiprocessing.Value('d', temperature)
    price, stockvar, war, tension, carbon, crisis, stop = 0.1765, 0, 0, 0, 0, 0, False
    stockvarbuffer = 0
    nbTransaction = 0

    # Locks
    lock = threading.Lock()
    lockWeather = threading.Lock()

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
                p = threading.Thread(target=changeStock, args=(mqMarket, message, lock))
                p.start()
                p.join()
                nbTransaction += 1
                break
            except sysv_ipc.BusyError:
                if stop:
                    break
                else:
                    pass
            try:
                tour, tt = mqMarket.receive(type=3, block=False)
                # Price calculation
                lockWeather.acquire()
                lock.acquire()
                stockvarbuffer = stockvar
                stockvar = 0
                lock.release()
                price = 0.999 * price + (1/10) * 1/(weatherTemp.value+25.1) - 0.0001*stockvarbuffer + (0.02 * war + 0.013 * tension + 0.008 * carbon + 0.017 * crisis)
                if price <= 0:
                    price = 0.0001
                lockWeather.release()

                print(tour.decode())

                print("Variation of stock is ", stockvarbuffer)
                print("The current price is ", round(price, 4), "€/kWh")
                print("The temperature is ", round(weatherTemp.value, 1), "°C\n")
            except sysv_ipc.BusyError:
                pass


        if stop:
            break

    # Proper end of the program when receiving control-C or SIGINT
    os.kill(pro.pid, signal.SIGTERM)
    os.kill(politic.pid, signal.SIGTERM)
    os.kill(economic.pid, signal.SIGTERM)
    mqHome.remove()
    mqMarket.remove()
    print("End of Simulation...\nPrice of energy market : ", round(price, 2), "€/Wh\nNumber of transactions in market :", nbTransaction)

