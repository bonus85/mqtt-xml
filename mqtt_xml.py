#!/usr/bin/env python
"""
@author: Sindre Tosse
"""
import json
from collections import deque

import cherrypy
import paho.mqtt.client as mqtt
from dicttoxml import dicttoxml


class MqttHandler:

    def __init__(self, config):
        self.config = config
        self.topics = config['topics']
        self.data = dict(
            (topic, deque(maxlen=config['history'])) for topic in self.topics)
        
        self.client = mqtt.Client()
        self.client.on_connect = self.mqtt_on_connect
        self.client.on_message = self.mqtt_on_message
        
        # Check for username/password auth
        try:
            username = config['mqtt_connection'].pop('username')
            password = config['mqtt_connection'].pop('password')
        except KeyError:
            pass
        else:
            self.client.username_pw_set(username, password)
        
    def mqtt_on_connect(self, client, userdata, flags, rc):
        for topic in self.topics:
            self.client.subscribe(topic)

    def mqtt_on_message(self, client, userdata, msg):
        cherrypy.log('Receieved mqtt message on topic {}'.format(msg.topic))
        try:
            message = json.loads(msg.payload)
        except ValueError:
            message = msg.payload
        self.data[msg.topic].append(message)

    def __enter__(self):
        cherrypy.log('Connecting to mqtt broker')
        self.client.connect(**self.config['mqtt_connection'])
        self.client.loop_start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.loop_stop()
        self.client.disconnect()
        cherrypy.log('Disconnected from mqtt broker')


class Endpoint:

    def __init__(self, mqtt_handler):
        self.mqtt_handler = mqtt_handler
        
    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'text/xml'
        return dicttoxml(self.mqtt_handler.data)

if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)
    mqtt_handler = MqttHandler(config)
    cherrypy.tree.mount(Endpoint(mqtt_handler), '/')

    cherrypy.engine.start()
    with mqtt_handler:
        cherrypy.log('Service started, press <ctrl> + C to exit')
        cherrypy.engine.block()
