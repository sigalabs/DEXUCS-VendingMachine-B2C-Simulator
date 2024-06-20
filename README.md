# DEX/UCS Vending Machine Simulator

Python script to simulate a vending machine (including Bean2Cup coffee machines) that communicates with a telemetry device over a serial port using the DEX/UCS protocol to transfer an EVADTS file.

## Features

- Simulates the DEX/UCS protocol communication between a vending machine (including Bean2Cup coffee machines) and a telemetry device.
- Handles the first and second handshake processes.
- Transfers the EVADTS file line by line.
- Allows the user to specify the serial COM port and the file path.

## Requirements

- Python 3.x
- `pyserial` library

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/SIGAlabs/DEX_UCS_VendingMachine_Simulator.git
   cd DEX_UCS_VendingMachine_Simulator
   ```

2. Install the required `pyserial` library:
   ```bash
   pip install pyserial
   ```

## Usage

1. Run the script:

   ```bash
   python dex_vending_machine_simulator.py
   ```

2. When prompted, enter the COM port and the path to the EVADTS file. Press Enter to use the default values.

   - Default COM port: `COM1`
   - Default EVADTS file path: `evadts.txt`

## Example

Enter the COM port (default COM1): COM5

Enter the path to the EVADTS file (default evadts.txt): c:\newevadts.txt

## Script Details

The script simulates the communication between a vending machine (including Bean2Cup coffee machines) and a telemetry device using the DEX/UCS protocol. It performs the following steps:

1. **First Handshake**:

   - Waits for an ENQ signal from the device.
   - Sends an ACK0 signal in response.
   - Reads the operation request message from the device.
   - Verifies the CRC of the received message.
   - Sends an ACK1 signal if the CRC is correct.
   - Waits for an EOT signal from the device.

2. **Second Handshake**:

   - Sends an ENQ signal to the device.
   - Waits for ACK0 and ACK1 signals from the device.
   - Sends the communication ID and revision level along with the CRC.
   - Sends an EOT signal.

3. **File Transfer**:
   - Sends an ENQ signal to the device.
   - Waits for an ACK0 signal.
   - Sends each line of the EVADTS file with the appropriate DLE, ETX, and ETB signals, calculating and appending the CRC for each line.
   - Waits for ACK0 or ACK1 signals for each line. Resends the line if a NAK signal is received.

## Supported Devices

- Standard vending machines with DEX/UCS communication
- Bean2Cup coffee machines with DEX/UCS communication

## Baudrate

The baudrate for the serial communication is hardcoded to `9600`. If your device requires a different baudrate, you will need to modify the `BAUDRATE` variable in the script.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or issues, please open an issue in the repository or contact SIGAlabs.
