import serial
import time

# Constants for DEX/UCS protocol
ENQ = b'\x05'  # Enquiry signal
EOT = b'\x04'  # End of Transmission
DLE = b'\x10'  # Data Link Escape
ACK0 = DLE + b'\x30'  # Acknowledge 0 (DLE0)
ACK1 = DLE + b'\x31'  # Acknowledge 1 (DLE1)
NAK = b'\x15'  # Negative Acknowledge
SOH = b'\x01'  # Start of Header
STX = b'\x02'  # Start of Text
ETX = b'\x03'  # End of Text
ETB = b'\x17'  # End of Transmission Block

# Communication details
BAUDRATE = 9600  # Baudrate for serial communication
DEXDELAY = 0.05  # Delay to handle timing issues

# Communication ID and Revision Level
VMD_CommunicationID = b'SWR0010001'  # Vending Machine Device Communication ID
VMD_RevisionLevel = b'R01L01'  # Revision Level

# Default values
DEFAULT_COM_PORT = 'COM1'
DEFAULT_FILE_PATH = 'evadts.txt'

def dex_crc16(dwCRC, byte):
    """Calculate the CRC16 for a given byte."""
    for j in range(8):
        DATA_0 = (byte >> j) & 0x01
        BCC_0 = dwCRC & 0x01
        BCC_1 = (dwCRC >> 1) & 0x01
        BCC_14 = (dwCRC >> 14) & 0x01
        X16 = BCC_0 ^ DATA_0
        X15 = BCC_1 ^ X16
        X2 = BCC_14 ^ X16
        dwCRC >>= 1
        dwCRC &= 0x5FFE
        dwCRC |= X15
        dwCRC |= X2 << 13
        dwCRC |= X16 << 15
    return dwCRC

def send_ack(serial_port, ack_type):
    """Send an ACK (acknowledge) signal."""
    print(f"Sending ACK: {ack_type.hex()}")
    serial_port.write(ack_type)
    serial_port.flush()

def send_enq(serial_port):
    """Send an ENQ (enquiry) signal."""
    print("Sending ENQ...")
    serial_port.write(ENQ)
    serial_port.flush()

def wait_for_enq(serial_port):
    """Wait for an ENQ (enquiry) signal."""
    print("Waiting for ENQ...")
    start_time = time.time()
    while time.time() - start_time < 300:  # Wait for 5 minutes for ENQ
        if serial_port.in_waiting > 0:
            data = serial_port.read(1)
            print(f"Received: {data.hex()}")
            if data == ENQ:
                return True
    return False

def wait_for_eot(serial_port):
    """Wait for an EOT (end of transmission) signal."""
    print("Waiting for EOT...")
    start_time = time.time()
    while time.time() - start_time < 5:  # Wait for 5 seconds for EOT
        if serial_port.in_waiting > 0:
            data = serial_port.read(1)
            print(f"Received: {data.hex()}")
            if data == EOT:
                return True
    return False

def wait_for_ack(serial_port, expected_ack):
    """Wait for an ACK (acknowledge) signal."""
    print(f"Waiting for ACK {expected_ack.hex()}...")
    start_time = time.time()
    while time.time() - start_time < 5:  # Wait for 5 seconds for ACK
        if serial_port.in_waiting >= 2:
            data = serial_port.read(2)
            print(f"Received: {data.hex()}")
            if data == expected_ack:
                return True
    return False

def dex_first_handshake(serial_port):
    """Perform the first handshake in the DEX protocol."""
    if not wait_for_enq(serial_port):
        print("First Handshake Error: ENQ not received")
        return False

    send_ack(serial_port, DLE + b'\x30')

    time.sleep(DEXDELAY)  # Small delay after sending ACK0

    # Read the device's operation request message
    message = bytearray()
    while True:
        byte = serial_port.read(1)
        message.append(byte[0])
        if len(message) >= 2 and message[-2:] == DLE + ETX:
            break

    crc_received = serial_port.read(2)
    crc_received_value = int.from_bytes(crc_received, byteorder='little')
    full_message = message + crc_received
    print(f"Received: {full_message.hex()}")

    # Verify the received message ends with the expected DLE + ETX + CRC
    if not message.endswith(DLE + ETX):
        print("First Handshake Error: Invalid message format received")
        return False

    # Calculate CRC of the received message
    crc_calculated = 0x0000
    for byte in message:
        if byte != DLE[0] and byte != SOH[0]:
            crc_calculated = dex_crc16(crc_calculated, byte)

    print(f"Received CRC: {crc_received_value:04x}, Calculated CRC: {crc_calculated:04x}")

    if crc_received_value != crc_calculated:
        print("First Handshake Error: CRC mismatch")
        return False
    
    send_ack(serial_port, DLE + b'\x31')

    if not wait_for_eot(serial_port):
        print("First Handshake Error: EOT not received")
        return False

    time.sleep(DEXDELAY)
    return True

def dex_second_handshake(serial_port):
    """Perform the second handshake in the DEX protocol."""
    send_enq(serial_port)

    if not wait_for_ack(serial_port, DLE + b'\x30'):
        print("Second Handshake Error: ACK0 not received")
        return False

    # Prepare the message with communication ID and revision level
    message = DLE + SOH + VMD_CommunicationID + b'R' + VMD_RevisionLevel + DLE + ETX

    # Calculate CRC
    crc = 0x0000
    for byte in message:
        crc = dex_crc16(crc, byte)
    crc_bytes = crc.to_bytes(2, 'little')

    # Send the message with CRC
    serial_port.write(message + crc_bytes)
    serial_port.flush()

    print(f"Sent: {message.hex()} with CRC: {crc_bytes.hex()}")

    if not wait_for_ack(serial_port, DLE + b'\x31'):
        print("Second Handshake Error: ACK1 not received after sending communication ID and revision level")
        return False

    time.sleep(DEXDELAY)

    serial_port.write(EOT)
    serial_port.flush()
    print("Sent EOT")

    return True

def dex_transfer_file(serial_port):
    """Transfer the EVADTS file using the DEX protocol."""
    send_enq(serial_port)
    if not wait_for_ack(serial_port, DLE + b'\x30'):
        print("Error: ACK0 not received before sending the first line")
        return

    for i, line in enumerate(evadts_file_lines):
        is_last_line = (i == len(evadts_file_lines) - 1)
        send_data_line(serial_port, line.strip() + '\r\n', i, is_last_line)  # Strip line endings

def send_data_line(serial_port, line, line_number, is_last_line):
    """Send a line of data from the EVADTS file."""
    # Ensure the data is sent in binary mode
    data_bytes = line.encode('utf-8')
    
    if is_last_line:
        data_bytes += DLE + ETX
    else:
        data_bytes += DLE + ETB

    print(f"Data bytes for CRC calculation: {data_bytes.hex()}")
    dwCRC = 0x0000
    for byte in data_bytes:
        if byte != DLE[0]:
            dwCRC = dex_crc16(dwCRC, byte)

    # Print the calculated CRC
    print(f"Calculated CRC: {dwCRC:04x}")

    # Prepare the message
    message = DLE + STX + data_bytes + dwCRC.to_bytes(2, 'little')

    print(f"Sending line {line_number}: {message.hex()}")
    serial_port.write(message)
    serial_port.flush()

    start_time = time.time()
    while time.time() - start_time < 5:
        if serial_port.in_waiting > 0:
            response = serial_port.read(2)
            print(f"Received: {response.hex()}")
            if response == ACK0 or response == ACK1:  # ACK0 or ACK1
                return
            elif response == NAK:
                print("NAK received, resending line")
                serial_port.write(message)
                serial_port.flush()
            time.sleep(DEXDELAY)
    print("Error: Did not receive ACK0, ACK1 or NAK in time")

def main():
    """Main function to initialize the serial port and perform DEX/UCS operations."""
    # Get the serial port and file path from the user
    com_port = input(f"Enter the COM port (default {DEFAULT_COM_PORT}): ") or DEFAULT_COM_PORT
    file_path = input(f"Enter the path to the EVADTS file (default {DEFAULT_FILE_PATH}): ") or DEFAULT_FILE_PATH

    # Load the EVADTS file
    with open(file_path, 'r') as file:
        global evadts_file_lines
        evadts_file_lines = file.readlines()  # Read all lines from the file

    while True:
        with serial.Serial(com_port, baudrate=BAUDRATE, timeout=1, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE) as serial_port:
            serial_port.reset_input_buffer()  # Clear the input buffer
            serial_port.reset_output_buffer()  # Clear the output buffer
            time.sleep(2)  # Allow time for the serial port to initialize

            if dex_first_handshake(serial_port):
                print("First handshake successful")

                if dex_second_handshake(serial_port):
                    print("Second handshake successful")

                    dex_transfer_file(serial_port)
                    print("File transfer completed")
                else:
                    print("Second handshake failed")
            else:
                print("First handshake failed")

            print("Restarting the process...")

if __name__ == "__main__":
    main()
