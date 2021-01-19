import sys
import os
import sysv_ipc
import multiprocessing
import random
import time
import signal

# Keys of both messages queues
keyMarket = 999
keyHome = 777


def maison(InitProd, ConsoRate, SalePol, mqhome, mqmarket, exchange):  # Home process
    i = 1

    if SalePol == 0:
        pol = "Always give away"
    elif SalePol == 1:
        pol = "Always sell on market"
    else:
        pol = "Sell if no takers"

    pid = os.getpid()
    print("Home energy trade policy", pid, " : ", pol)

    while True:

        # Allow to display the laps with just one process before go to execute the transactions
        cond = b.wait()

        try:
            # Remove the messages from the previous turn
            mqhome.receive(type=2, block=False)
        except sysv_ipc.BusyError:
            pass

        if cond == 0:
            print("Tour ", i)
        b.wait()

        # Display home's characteristics
        print("Home ", pid, " | Consumption : ", ConsoRate, " | Production : ", InitProd, "\n")

        # If consumption is superior to production, we send a request to the Message Queue between homes
        if ConsoRate > InitProd:
            Quantity = ConsoRate - InitProd
            m1 = "%d,%d" % (pid, Quantity)
            m2 = m1.encode()
            mqhome.send(m2, type=2) # Send a request

            try:
                # Waiting for an answer from an home
                time.sleep(5)
                rep, t = mqhome.receive(type=pid, block=False)
                print(rep.decode())
                lock.acquire()
                exchange.value = exchange.value + 1
                lock.release()

            # If no answers
            except sysv_ipc.BusyError:
                m = "%d,%d" % (pid, -Quantity)
                m = m.encode()
                mqmarket.send(m, type=1)  # Sending a sales request to the market
                # ACK reception, if no ACKn then simulation blocked
                m, t = mqmarket.receive(type=pid)


        # Case of excess energy
        elif ConsoRate < InitProd:
            surplus = InitProd - ConsoRate
            # If energy trade policy is: Always give away
            if SalePol == 0:
                try:
                    # Waiting for a request
                    time.sleep(1)
                    # Request reception
                    m, t = mqhome.receive(type=2, block=False)
                    dem = m.decode()
                    # We get back the PID of the home which needs energy
                    pidm, quantitym = dem.split(",")
                    quantitym = int(quantitym)
                    reponse = "Donation achieved"
                    # If surplus, we carry out the donation with sending an ACK
                    if surplus >= quantitym:
                        mqhome.send(reponse.encode(), type=int(pidm))
                        surplus -= quantitym
                    # If not enough energy, we put the request back in the message queue with the surplus
                    else:
                        mqhome.send(m)
                except sysv_ipc.BusyError:
                    pass

            # If energy trade policy is: Always sell on the market
            elif SalePol == 1:
                # Send Message in MQ to the Market
                m = "%d,%d" % (pid, surplus)
                m = m.encode()
                # Send the sales
                mqmarket.send(m, type=1)
                # ACK reception from market
                mqmarket.receive(type=pid)

            # If energy trade policy is: Sell if no takers
            elif SalePol == 2:
                # Donor state
                try:
                    time.sleep(1)
                    m, t = mqhome.receive(block=False, type=2)
                    dem = m.decode()
                    pidm, quantitym = dem.split(",")
                    quantitym = int(quantitym)
                    reponse = "Donation achieved"
                    if surplus >= quantitym:
                        mqhome.send(reponse.encode(), type=int(pidm))
                        surplus -= quantitym
                    else:
                        mqhome.send(m)
                # Seller state
                except sysv_ipc.BusyError:
                    m = "%d,%d" % (pid, surplus)
                    m = m.encode()
                    mqmarket.send(m, type=1)
                    msg, t = mqmarket.receive(type=pid)

        # Modification of each home's values + lap incrementation
        InitProd = random.randrange(100, 1000, 100)
        ConsoRate = random.randrange(100, 1000, 100)

        cond2 = b.wait()
        if cond2 == 0:
            numTour = "Tour %d" % i
            mqmarket.send(numTour.encode(), type=3)
        i += 1


if __name__ == "__main__":

    # Connexions to the MQ
    try:
        mqmarket = sysv_ipc.MessageQueue(keyMarket)
    except sysv_ipc.ExistentialError:
        print("Cannot connect to MQ", keyMarket)
        sys.exit(1)

    try:
        mqhome = sysv_ipc.MessageQueue(keyHome)
    except sysv_ipc.ExistentialError:
        print("Cannot connect to MQ", keyHome)
        sys.exit(1)

    # Home number recuperation
    nMaison = int(sys.argv[1])
    # Synchro barrier creation
    b = multiprocessing.Barrier(nMaison)
    # Home PID table
    pidProcesses = []
    # Lock and shared variable nbEchange to count the donations
    lock = multiprocessing.Lock()
    nbEchange = 0
    homeExchange = multiprocessing.Value('d', nbEchange)

    # Launch of houses
    for x in range(nMaison):
        InitProd = random.randrange(100, 1000, 100)
        ConsoRate = random.randrange(100, 1000, 100)
        # 0 to Always give away, 1 to Always sell, 2 to Sell if no takers
        SalePol = random.randrange(0, 3, 1)
        p = multiprocessing.Process(target=maison, args=(InitProd, ConsoRate, SalePol, mqhome, mqmarket, homeExchange))
        p.start()
        print("PID ", p.pid)
        pidProcesses.append(p.pid)

    # Waiting loop for simulation end
    while True:
        try:
            mqmarket.receive(type=2, block=False)
            print("Ending Simulation...")
            # End of homes processes
            for x in range(nMaison):
                print("Home ", pidProcesses[x], "is stopped")
                os.kill(pidProcesses[x], signal.SIGTERM)
            # Send ACK to close the simulation
            mqmarket.send(b"", type=3)
            break
        except sysv_ipc.BusyError:
            pass

    print("End of Simulation\nNumber of exchanges between homes : ", homeExchange.value)
















