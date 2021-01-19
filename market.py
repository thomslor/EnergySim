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
        time.sleep(2)
        mutex.acquire()
        temp.value = temp.value + random.gauss(0, 4)
        if temp.value >= 45:
            temp.value = 40
        elif temp.value <= -30:
            temp.value = -25
        mutex.release()
        # print("WEATHER: Temperature is ", temp.value)


def politics():  # Process politics: send randomly signals (SIGUSR1 & SIGUSR2) to market
    print("Politics PID: ", os.getpid())
    pid = int(os.getppid())
    while True:
        time.sleep(10)
        random.randrange(0, 100)
        if random.randrange(0, 100) <= 20:
            os.kill(pid, signal.SIGUSR2)
        elif 20 < random.randrange(0, 100) <= 50:
            os.kill(pid, signal.SIGUSR1)


def economics():  # Process economics: send randomly signals (SIGILL & SIGPIPE) to market
    print("Economics PID: ", os.getpid(), "\n")
    pid = int(os.getppid())
    while True:
        time.sleep(10)
        ca, cr = random.randrange(0, 100), random.randrange(0, 100)
        if ca <= 30:
            os.kill(pid, signal.SIGILL)
        if cr <= 30:
            os.kill(pid, signal.SIGPIPE)


def handler(sig, frame):  # Handle signals and modify values regarding the signal received
    global war, tension, carbon, crisis, stop, mqMarket
    if sig == signal.SIGUSR2:
        if war == 0:
            print("*****WAR BEGINS*****")
            if tension == 1:
                print("*****AND ERASES TENSIONS*****")
        else:
            print("*****WAR ENDS*****")
        war = (war+1) % 2
        tension = 0
    elif sig == signal.SIGUSR1:
        if tension == 0:
            print("*****DIPLOMATIC TENSIONS*****")
        else:
            print("*****NO MORE TENSIONS*****")
        tension = (tension+1) % 2
    if sig == signal.SIGILL:
        if carbon == 0:
            print("*****CARBON RAISES*****")
        else:
            print("*****CARBON DECREASES*****")
        carbon = (carbon+1) % 2
    if sig == signal.SIGPIPE:
        if crisis == 0:
            print("*****HUGE CRISIS*****")
        else:
            print("*****REGROWTH AFTER CRISIS*****")
        crisis = (crisis+1) % 2
    if sig == signal.SIGINT:  # Use to proper stop the program when receiving control-C or SIGINT
        os.kill(pro.pid, signal.SIGTERM)
        os.kill(politic.pid, signal.SIGTERM)
        os.kill(economic.pid, signal.SIGTERM)
        mqMarket.send(b"", type=2)
        print("maison.py is ending...")
        mqMarket.receive(type=3)
        stop = True


def changeStock(mq, msg, mutex):  # Change the stock according to the homes
    # print("Starting thread:", threading.current_thread().name)
    global stock
    msg = msg.decode()
    # print("msg is ", msg)
    pid, value = msg.split(",")
    pid, value = int(pid), int(value)
    if value > 0:  # Home wants to sell
        mutex.acquire()
        stock = stock + value
        mutex.release()
        typeTransaction = "Sales"
    elif value < 0:  # Home wants to buy
        mutex.acquire()
        stock = stock + value
        mutex.release()
        typeTransaction = "Purchase"
    mq.send(b"", type=pid)  # Send an ACK
    print("Transaction with Home ", pid, ", ", typeTransaction, ", stock is now :", str(stock))
    # print("Ending thread:", threading.current_thread().name)


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
    price, stock, war, tension, carbon, crisis, stop = 15, 100000, 0, 0, 0, 0, False
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
                # print(message)
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

        # Price calculation
        lockWeather.acquire()
        print("price:", price, "temperature:", weatherTemp.value, "war:", war, "tension:", tension, "carbon:", carbon, "crisis:", crisis)
        price = 0.9 * price + weatherTemp.value*(-0.5) + (20 * war + 13 * tension + 8 * carbon + 17 * crisis)
        if price <= 0:
            price = 0.5
        lockWeather.release()

        print("The current price is ", round(price, 2), "€/Wh")
        print("The temperature is ", round(weatherTemp.value, 1), "°C\n")
        # print("Stop is ", stop)
        if stop:
            break

    # Proper end of the program when receiving control-C or SIGINT
    mqHome.remove()
    mqMarket.remove()
    print("End of Simulation...\nPrice of energy market : ", round(price, 2), "€/Wh\nNumber of transactions in market :", nbTransaction)

