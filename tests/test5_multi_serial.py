from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.serialInterface import serial_client
from sample.utils import config_loader
from sample.core import controller
from sample.core import scheduler
import threading

def main():
    controller.routine1()
    # threading.Thread(target=controller.routine1(), daemon=True).start()
    
if __name__ == "__main__":
    main()