import sys
import sysv_ipc




if __name__ == "__main__":
    InitProd = int(sys.argv[1])
    ConsoRate = int(sys.argv[2])
    SalePol = int(sys.argv[3]) # 0 pour Toujours Donner, 1 pour Toujours Vendre, 2 pour Vendre si personne prend

    if ConsoRate > InitProd:
        Quantity = ConsoRate - InitProd

    elif ConsoRate < InitProd:
        if SalePol == 0:
            # Attendre Message dans MQ entre Home
        elif SalePol == 1:
            # Envoyer Message dans MQ vers Market
        elif SalePol == 2:
            # Attendre Demande pendant X sec, si pas de réponse alors envoyer



