import serial
import threading
import queue
import concurrent.futures
import logging
import binascii

from datetime import datetime, timedelta
from time import sleep

logging.getLogger().setLevel(logging.DEBUG)

sRS = b'\x1E'    #<RS> Record Separator
sSTX = b'\x02'   #<STX> Start of Text
sEOT = b'\x04'   #<EOT> End of Transmission
sETX = b'\x03'   #<ETX> End of Text
sCR = b'\x0D'    #<CR> Carriage Return
sACK = b'\x06'   #<ACK> Acknowledge
sNAK = b'\x15'   #<NAK> Negative Acknowledge
sESC = b'\x1B'   #<ESC> Escape

def xchksum(string):
        """
            The CheckSum is the Ascii Character of the XOR of all the Previous Bits
        :param cr:
        :param uid:
        :param txt: String fuente
        :param context:
        :return: Caracter ASCII  del XOR CHECKSUM
        """
        checksum = 0
        for el in string:
            checksum ^= ord(el)
        checksum &= 63  # '[AND] it to keep the lower 6 bits
        checksum |= 64  # '[OR] it to make it printable.
        return chr(checksum)

def send_command(ser, command):
    """
    Send a command to the serial port
    :param ser: Serial port object
    :param command: Command to send
    :return: None
    """
    # Add the checksum
    to_send = build_feedline(command)
    logging.info('Formated data: %s', to_send)
    ser.write(to_send)
    # Read the response
    response = ser.read(1)
    return response

def build_feedline(data):
    data_edit = data.replace('\n', '') + '\x0D'
    data_hex = data_edit.encode()
    checksum = xchksum(data_edit).encode()
    return sESC + b'Rd' + sSTX + data_hex + sETX + checksum + sEOT

def receive_data(ser, queue, startEvent, receiveEvent):
    while startEvent.is_set():
        data = ser.read(119)
        logging.info('Data received: %s', data)
        queue.put(data)
    logging.info('Receive is done')

def store_data(queue, receiveEvent):
    while receiveEvent.is_set():
        threading.Event().wait(1)
        if not queue.empty():
            data = queue.get()
            logging.info('Storing data: %s (size=%d)', data, queue.qsize())
    logging.info('Storing is done')

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")

    pipeline = queue.Queue()
    startevent = threading.Event()
    storeevent = threading.Event()

    with serial.Serial(port='COM1', baudrate=9600, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=10) as ser:
        logging.info('Serial port opened, sending PC command')
        ser.write(sESC + b'CcE' + sEOT)
        ans = ser.read(1)
        if ans != sACK:
            logging.error('Error opening PC communication')
        else:
            with open('data.txt') as file:
                for line in file:
                    logging.info('Original data: %s', line)
                    output = send_command(ser, line)
                    if output != sACK:
                        logging.error('Error sending data: %s', line)
                    else:
                        logging.info('Data received by indicator')
                    sleep(0.5)
                logging.info('Data sent')
            logging.info('Starting information retrieval')
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                startevent.set()
                storeevent.set()
                executor.submit(receive_data, ser, pipeline, startevent, storeevent)
                executor.submit(store_data, pipeline, storeevent)
                try:
                    while True:
                        sleep(2)
                except KeyboardInterrupt:
                    startevent.clear()
                    storeevent.clear()
        logging.info('Main done')
    logging.info('Closing serial port')

