# BSB Controller

BSB Controller is a tool designed for configuring and monitoring the BSB-featured boilers via MQTT.
It is suited for Baxi Luna Platinum boilers, but will work with any other BSB based boilers.

## Features

- **Boiler configuration and monitoring**: 
- **Home Assistant integration**: MQTT integration featuring HA MQTT discovery for seamless configuration
- **Debug Monitoring Interface**: Simple get/set/log interface through HTTP/JSON.
- **Configurable and expandable**: User-selectable messages and period for their refresh
- **Minimal hardware required**: Python-enabled system with serial port and simple hardware adapter / voltage level convertor

## Getting Started

### Prerequisites

- Python 3.x
- MQTT broker (e.g., Mosquitto)
- System with serial port capable "odd parity".
- Hardware adapter for serial port
- Home Assistant (optional)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/martinspinler/bsb-controller.git
   cd bsb-controller
   
2. **Install dependencies:**
   It's recommended to use a virtual environment:
   
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
3. **Configure the application:**
   Edit example configuration in example.yaml file.
   
4. **Run the application:**
   
   ```bash
   python -m bsbcontroller --config examle.yaml

## Usage


## Hardware adapter



## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
