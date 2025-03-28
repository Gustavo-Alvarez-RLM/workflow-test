import serial
import threading
from time import sleep, time

# Configuration
SERIAL_PORT = 'COM1'  # Change this to your serial port
BAUD_RATE = 9600
READ_MODE_DURATION = 10  # Seconds
WRITE_MODE_DURATION = 10  # Seconds

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, timeout=1)

# Function to read from the serial port
def read_from_serial():
    while running:
        if mode == 'read':
            if ser.in_waiting > 0:
                data = ser.readline()
                print(f"Read: {data}")

# Function to write to the serial port
def write_to_serial():
    while running:
        if mode == 'write':
            message = "Hello, Serial Port!\n"
            ser.write(message.encode('utf-8'))
            print(f"Wrote: {message.strip()}")
            sleep(1)  # Adjust this delay as needed

# Function to switch modes based on elapsed time
def switch_mode():
    global mode
    start_time = time()
    while running:
        elapsed_time = time() - start_time
        if mode == 'read' and elapsed_time >= READ_MODE_DURATION:
            mode = 'write'
            start_time = time()
            print("Switched to write mode")
        elif mode == 'write' and elapsed_time >= WRITE_MODE_DURATION:
            mode = 'read'
            start_time = time()
            print("Switched to read mode") 
        sleep(1)  # Check every second

# Main function
if __name__ == "__main__":
    mode = 'read'
    running = True

    # Start threads for reading, writing, and switching modes
    read_thread = threading.Thread(target=read_from_serial)
    write_thread = threading.Thread(target=write_to_serial)
    switch_thread = threading.Thread(target=switch_mode)

    read_thread.start()
    write_thread.start()
    switch_thread.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        running = False
        read_thread.join()
        write_thread.join()
        switch_thread.join()
        ser.close()
        print("Program terminated")