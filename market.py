import sys
import sysv_ipc


key = 999

if __name__ == "__main__":
    price, stock, war, tension, carbon, crisis = 1, 0, 0, 0, 0, 0
    price = 0.9*price + (0.2*war + 0.5*tension + 0.5*carbon + 0.5*crisis)  #random coeff

    try:
        mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
    except ExistentialError:
        print("Message queue", key, "already exsits, terminating.")
        sys.exit(1)