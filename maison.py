import sys
import os
import sysv_ipc
import multiprocessing
import random
import time


keyMarket = 999
keyHome = 777

def maison(InitProd, ConsoRate, SalePol, mqhome, mqmarket):
    i=1

    while True:
        cond = b.wait()
        if cond == 0:
            print("Tour ", i)
        b.wait()
        pid = os.getpid()
        print("Maison ", pid, " | Consommation : ", ConsoRate, " | Production : ", InitProd, "\n")

        if ConsoRate > InitProd:  # Implémenter un boucle pour accéder à retour à la normale (tant que j'ai pas recu le bon message, récupérez des messages)
            Quantity = ConsoRate - InitProd
            m1 = "%d,%d" % (pid, Quantity)
            m2 = m1.encode()
            mqhome.send(m2, type=2)

            try:
                time.sleep(5)
                rep, t = mqhome.receive(type=pid, block=False)
                print(rep.decode())
            except sysv_ipc.BusyError:
                m = "%d,%d" % (pid, -Quantity)
                m = m.encode()
                mqmarket.send(m, type=1)
                m, t = mqmarket.receive(type=pid)
                #print("m2 is ", m, "\n")



        elif ConsoRate < InitProd:
            surplus = InitProd - ConsoRate
            if SalePol == 0:
                try:
                    time.sleep(2)
                    m, t = mqhome.receive(type=2, block=False)
                    dem = m.decode()
                    pidm, quantitym = dem.split(",")
                    # print("Le PID de la demande = ", pidm, "\nLa Quantité demandée = ", quantitym)
                    quantitym = int(quantitym)
                    reponse = "Don réalisé"
                    if surplus >= quantitym:
                        mqhome.send(reponse.encode(), type=int(pidm))
                        surplus -= quantitym
                    else:
                        mqhome.send(m)
                except sysv_ipc.BusyError:
                    pass


            elif SalePol == 1:
                # Envoyer Message dans MQ vers Market
                m = "%d,%d" % (pid, surplus)
                #print("send is ", m, "\n")
                m = m.encode()
                #print(pid)
                mqmarket.send(m, type=1)
                msg, t = mqmarket.receive(type=pid)
                #print("response is ", msg, "\n")


            elif SalePol == 2:
                try:
                    while surplus > 0:
                        time.sleep(3)
                        m, t = mqhome.receive(block=False, type=2)
                        dem = m.decode()
                        pidm, quantitym = dem.split(",")
                        #print("Le PID de la demande = ", pidm, "\nLa Quantité demandée = ", quantitym)
                        quantitym = int(quantitym)
                        if surplus >= quantitym:
                            #print(pidm.encode())
                            mqhome.send(pidm.encode(), type=1)
                        else:
                            mqhome.send(m)
                except sysv_ipc.BusyError:
                    m = "%d,%d" % (pid, surplus)
                    #print("send is ", m, "\n")
                    m = m.encode()
                    #print(pid)
                    mqmarket.send(m, type=1)
                    msg, t = mqmarket.receive(type=pid)
                    #print("response is ", msg, "\n")

        InitProd = random.randrange(100, 1000, 100)
        ConsoRate = random.randrange(100, 1000, 100)
        i+=1







if __name__ == "__main__":
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

    nMaison = int(sys.argv[1])
    b = multiprocessing.Barrier(nMaison)

    for x in range(nMaison):
        InitProd = random.randrange(100, 1000, 100)
        ConsoRate = random.randrange(100, 1000, 100)
        SalePol = random.randrange(0, 2, 1)  # 0 pour Toujours Donner, 1 pour Toujours Vendre, 2 pour Vendre si personne prend
        p = multiprocessing.Process(target=maison, args=(InitProd, ConsoRate, SalePol, mqhome, mqmarket))
        p.start()

        # Mettre la barrière dans une boucle et faire le print Tour suivant !
"""
    while True:

        try:
            mqmarket.receive(type=0, block=False)
            print("Marché Down")
            for x in range(nMaison):
                p.join()

            mqmarket.remove()
            mqhome.remove()
            sys.exit(1)
        except sysv_ipc.BusyError:
            pass
"""















