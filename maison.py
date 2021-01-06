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



    if ConsoRate > InitProd:
        Quantity = ConsoRate - InitProd
        m1 = "%d,%d" % (pid, Quantity)
        m2 = m1.encode()
        mqhome.send(m2)



    elif ConsoRate < InitProd:
        if SalePol == 0:
            m, t = mqhome.receive()
            m = m.decode()
            pidm, quantitym = m.split(",")
            print("Le PID de la demande = ", pidm, "\nLa Quantité demandée = ", quantitym)
            """
        elif SalePol == 1:
            #Envoyer Message dans MQ vers Market
        elif SalePol == 2:
            #Attendre Demande pendant X sec, si pas de réponse alors envoyer
"""


