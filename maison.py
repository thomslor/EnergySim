import sys
import os
import sysv_ipc


keyMarket = 999
keyHome = 777

if __name__ == "__main__":

    InitProd = int(sys.argv[1])
    ConsoRate = int(sys.argv[2])
    SalePol = int(sys.argv[3]) # 0 pour Toujours Donner, 1 pour Toujours Vendre, 2 pour Vendre si personne prend
    pid = os.getpid()

    try:
        mqmarket = sysv_ipc.MessageQueue(keyMarket)
    except ExistentialError:
        print("Cannot connect to MQ", keyMarket)
        sys.exit(1)


    try:
        mqhome = sysv_ipc.MessageQueue(keyHome)
    except ExistentialError:
        print("Cannot connect to MQ", keyHome)
        sys.exit(1)



    if ConsoRate > InitProd: #Implémenter un boucle pour accéder à retour à la normale (tant que j'ai pas recu le bon message, récupérez des messages)
        Quantity = ConsoRate - InitProd
        m1 = "%d,%d" % (pid, Quantity)
        m2 = m1.encode()
        mqhome.send(m2, type = 2)
        rep, t = mqhome.receive(type = 1)
        pidrep = rep.decode()
        print(pidrep) #Pose Problème
        if int(pidrep) == pid:
            print("Retour à la normale")
        else:
            mqhome.send(rep, type = 1)


    elif ConsoRate < InitProd:
        surplus = InitProd - ConsoRate
        if SalePol == 0:
            m, t = mqhome.receive(type = 2)
            dem = m.decode()
            pidm, quantitym = dem.split(",")
            print("Le PID de la demande = ", pidm, "\nLa Quantité demandée = ", quantitym)
            quantitym = int(quantitym)
            if surplus >= quantitym:
                print(pidm.encode())
                mqhome.send(pidm.encode(), type = 1)
            else:
                mqhome.send(m)

        elif SalePol == 1:
            #Envoyer Message dans MQ vers Market
            m = "1,%d" % surplus
            m = m.encode()
            mqmarket.send(m, type=pid)
            m, t = mqmarket.receive(type=pid)
"""
        elif SalePol == 2:
            #Attendre Demande pendant X sec, si pas de réponse alors envoyer
"""


