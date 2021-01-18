import sys
import os
import sysv_ipc
import multiprocessing
import random
import time
import signal

# Clés des 2 Messages Queues
keyMarket = 999
keyHome = 777


def maison(InitProd, ConsoRate, SalePol, mqhome, mqmarket):  # Processus Maison
    global nbEchange
    i = 1

    if SalePol == 0:
        pol = "Toujours Donner"
    elif SalePol == 1:
        pol = "Toujours Vendre"
    else:
        pol = "Adaptatible"

    pid = os.getpid()
    print("Politique d'échange de maison ", pid, " : ", pol)

    while True:
        #Permet de faire en sorte qu'un seul processus maison affiche le numéro du Tour avant de passer à l'execution des transactions
        cond = b.wait()
        if cond == 0:
            print("Tour ", i)
        b.wait()

        #Affichage des caractéristiques de la Maison

        print("Maison ", pid, " | Consommation : ", ConsoRate, " | Production : ", InitProd, "\n")


        #Si la Consommation est supérieur à la production, on envoie une demande dans la Message Queue entre les maisons
        if ConsoRate > InitProd:
            Quantity = ConsoRate - InitProd
            m1 = "%d,%d" % (pid, Quantity)
            m2 = m1.encode()
            #envoi de la demande
            mqhome.send(m2, type=2)

            try:
                #Attente d'une réponse d'une maison
                time.sleep(5)
                rep, t = mqhome.receive(type=pid, block=False)
                print(rep.decode())
                lock.acquire()
                nbEchange += 1
                lock.release()
            #Si pas de réponse
            except sysv_ipc.BusyError:
                m = "%d,%d" % (pid, -Quantity)
                m = m.encode()
                # envoi d'une demande d'achat au market
                mqmarket.send(m, type=1)
                # Réception de l'ACK, si pas d'ACK, simulation bloquée
                m, t = mqmarket.receive(type=pid)
                # print("m2 is ", m, "\n")

        # Cas de surplus d'énergie
        elif ConsoRate < InitProd:
            surplus = InitProd - ConsoRate
            # Cas Toujours Donner le surplus
            if SalePol == 0:
                try:
                    # Attente d'une demande
                    time.sleep(1)
                    # Réception d'une demande
                    m, t = mqhome.receive(type=2, block=False)
                    dem = m.decode()
                    #On récupère le PID de la maison qui a besoin d'énergie
                    pidm, quantitym = dem.split(",")
                    quantitym = int(quantitym)
                    reponse = "Don réalisé"
                    #Si on a assez de surplus, on effectue le don en envoyant un ACK
                    if surplus >= quantitym:
                        mqhome.send(reponse.encode(), type=int(pidm))
                        surplus -= quantitym
                    #Si pas assez on remet la demande dans la message queue en ayant donné son surplus
                    else:
                        m1 = "%s,%d" % (pidm, quantitym-surplus)
                        m1 = m1.encode()
                        mqhome.send(m1)
                except sysv_ipc.BusyError:
                    pass

            #Cas Toujours Vendre
            elif SalePol == 1:
                # Envoyer Message dans MQ vers Market
                m = "%d,%d" % (pid, surplus)
                m = m.encode()
                # Envoi de la vente
                mqmarket.send(m, type=1)
                # Réception de l'ACK du market
                mqmarket.receive(type=pid)

            #Cas adaptable
            elif SalePol == 2:
                try:
                    #Phase Donneur
                    time.sleep(1)
                    m, t = mqhome.receive(block=False, type=2)
                    dem = m.decode()
                    pidm, quantitym = dem.split(",")
                    # print("Le PID de la demande = ", pidm, "\nLa Quantité demandée = ", quantitym)
                    quantitym = int(quantitym)
                    if surplus >= quantitym:
                        # print(pidm.encode())
                        mqhome.send(pidm.encode(), type=1)
                    else:
                        m1 = "%s,%d" % (pidm, quantitym-surplus)
                        m1 = m1.encode()
                        mqhome.send(m1)
                #Phase Vendeur
                except sysv_ipc.BusyError:
                    m = "%d,%d" % (pid, surplus)
                    # print("send is ", m, "\n")
                    m = m.encode()
                    # print(pid)
                    mqmarket.send(m, type=1)
                    msg, t = mqmarket.receive(type=pid)
                    # print("response is ", msg, "\n")

        #Modification des valeurs pour chaque maison + Incrément du tour
        InitProd = random.randrange(100, 1000, 100)
        ConsoRate = random.randrange(100, 1000, 100)
        i += 1


if __name__ == "__main__":

    #Connexions aux MQ
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

    #Récupération du nombre de maisons
    nMaison = int(sys.argv[1])
    #Création de la barrière de synchro
    b = multiprocessing.Barrier(nMaison)
    #Tableau des PID des maisons
    pidProcesses = []
    #Lock et Variable partagée nbEchange pour compter les dons
    lock = multiprocessing.Lock()
    nbEchange = 0

    #Lancement des maisons
    for x in range(nMaison):
        InitProd = random.randrange(100, 1000, 100)
        ConsoRate = random.randrange(100, 1000, 100)
        SalePol = random.randrange(0, 3, 1)  # 0 pour Toujours Donner, 1 pour Toujours Vendre, 2 pour Vendre si personne prend
        p = multiprocessing.Process(target=maison, args=(InitProd, ConsoRate, SalePol, mqhome, mqmarket))
        p.start()
        print("PID ", p.pid)
        pidProcesses.append(p.pid)

    #Boucle d'attente de fin de simulation
    while True:
        try:
            mqmarket.receive(type=2, block=False)
            print("Ending Simulation...")
            n = 0
            #Fin des process maisons
            for x in range(nMaison):
                print(pidProcesses[x])
                os.kill(pidProcesses[x], signal.SIGTERM)
                # p.join()
                n += 1
            #Envoi de l'ACK pour fermeture de simulation
            mqmarket.send(b"", type=3)
            break
        except sysv_ipc.BusyError:
            pass
    print("End of Simulation\nNumber of exchanges between homes : ", nbEchange)
















