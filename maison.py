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
        print("Message queue", keyMarket, "already exsits, terminating.")
        sys.exit(1)

    try:
        mqhome = sysv_ipc.MessageQueue(keyHome, sysv_ipc.IPC_CREX)
    except ExistentialError:
        print("Message queue", keyHome, "already exsits, terminating.")
        sys.exit(1)



    if ConsoRate > InitProd:
        Quantity = ConsoRate - InitProd
        m1 = str(pid), ",", str(Quantity)
        m2 = m1.encode()
        mqhome.send(m2)



    elif ConsoRate < InitProd:
        if SalePol == 0:
            m, t = mqhome.receive()
            print(t)
            """
        elif SalePol == 1:
            #Envoyer Message dans MQ vers Market
        elif SalePol == 2:
            #Attendre Demande pendant X sec, si pas de réponse alors envoyer
"""


