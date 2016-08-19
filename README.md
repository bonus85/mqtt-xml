# mqtt-xml
MQTT adapter with httm/xml endpoint

## Setup
1. Install python 2.7 + pip
2. Install the required packages by running  `pip install cherrypy dicttoxml paho-mqtt`
3. Configure the connection and topics in `config.json`

## Usage
Run with `python mqtt_xml.py` (`config.json` must be in the run directory). The last 5 messages sent to each topic is available in xml format on `localhost:8080`. The number of messages kept can be configured with the `history` parameter in `config.json`. Runtime modifications to subscribed topics is not possible.

Note that the program requires a local mqtt broker to be run as-is. The broker `mosquitto` is suitable for this purpose.

### Password protected brokers
Password protected MQTT brokers can be connected to by adding the parameters `username` and `password` to `mqtt_connection` in `config.json`.
