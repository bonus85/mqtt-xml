#!/usr/bin/env python
"""
@author: Sindre Tosse
"""
import json
import threading
from collections import deque

import cherrypy
import paho.mqtt.client as mqtt

class MqttHandler:

    def __init__(self, config, credentials=None):
        self.topics = []
        self.topic_lock = threading.Lock()
        
        self.client = mqtt.Client()
        if credentials is not None:
            self.client.username_pw_set(*credentials)
        self.client.on_connect = self.mqtt_on_connect
        self.client.on_message = self.mqtt_on_message
    
    def add_topic(self, topic):
        if topic.topic in self.topics:
            raise NotImplementedError(
                "Multiple topics on topic not supported")
        with self.topic_lock:
            self.topics.append(topic)
        self.client.subscribe(topic)
        
    def mqtt_on_connect(self, client, userdata, flags, rc):
        for topic in self.topics:
            self.client.subscribe(topic)

    def mqtt_on_message(self, client, userdata, msg):
        cherrypy.log('Receieved mqtt message on topic {}'.format(msg.topic))
        try:
            message = json.loads(msg.payload)
        except ValueError:
            message = msg.payload
        try:
            topic = self.topics[msg.topic]
        except KeyError:
            cherrypy.log('topic not found')
            return
        try:
            response = topic.request(message)
            cherrypy.log('Response: {}'.format(response))
        except Exception:
            cherrypy.log('There was an error in executing a request')

    def __enter__(self):
        cherrypy.log('Connecting to mqtt broker')
        self.client.connect(**MQTT_CONNECTION_PARAMETERS)
        self.client.loop_start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.loop_stop()
        self.client.disconnect()
        cherrypy.log('Disconnected from mqtt broker')

class Endpoint:

    exposed = True

    def __init__(self, mqtt_handler):
        self.mqtt_handler = mqtt_handler

    def GET(self, ta, dev_id, dev_type, endpoint_id):
        topic = EVENT_TOPIC.format(ta, dev_id, dev_type, endpoint_id)
        topic = mqtt_handler.get_topic(topic)
        return topic.to_dictionary()

    def POST(self, ta, dev_id, dev_type, endpoint_id):
        raise NotImplementedError("POST not implemented")

    def PUT(self, ta, dev_id, dev_type, endpoint_id):
        raise NotImplementedError("PUT not implemented")

    def DELETE(self, ta, dev_id, dev_type, endpoint_id):
        raise NotImplementedError("DELETE not implemented")

if __name__ == '__main__':
    mqtt_handler = MqttHandler()
    cherrypy.tree.mount(
        Endpoint(mqtt_handler), '/data',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    with mqtt_handler:
        cherrypy.engine.block()
