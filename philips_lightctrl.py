
#http://www.developers.meethue.com/documentation/lights-api

from phue import Bridge
from rgb_cie import Converter
import datetime
import socket
import argparse

class Light():
    def __init__(self, associated_bridge, bridge_light_id):
        self.bridge = associated_bridge
        self.lid = bridge_light_id
        self._create_colors()
        self.bri = 254
        self.color = 'white'
        self.last_reachable_status = None
        
    def _create_colors(self):
        c = Converter()
        self.colors = {
            'red': (c.rgbToCIE1931(1,0,0), 'xy'),
            'green': (c.rgbToCIE1931(0,1,0), 'xy'),
            'blue': (c.rgbToCIE1931(0,0,1), 'xy'),
            'yellow': (c.rgbToCIE1931(1,1,0), 'xy'),
            'orange': (c.rgbToCIE1931(1,0.49,0), 'xy'),
            'white': (353, 'ct')
            }
        
    def __str__(self):
        return "{:<30}{:<20}".format(self.name, "yes" if self.reachable() else "no")
    
    @property
    def name(self):
        try:
            return self.cached_name
        except AttributeError:
            self.cached_name = self._get('name')
        return self.cached_name

    @name.setter
    def name(self, value):
        self._set('name', value)
        self.cached_name = self._get('name')
        if self.cached_name != value:
            print("ERROR: Failed to set name")
        
    def reachable(self):
        return self.bridge.get_light(self.lid, 'reachable')

    def print_connection_status_updates(self):
        reachable = self.reachable()
        if self.last_reachable_status != reachable:
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M")
            self.last_reachable_status = reachable
            name = self.bridge.get_light(self.lid, 'name')
            print("{}: {} is now {}".format(
                timestamp, name, "reachable" if reachable else "out of range"))

    def transmit_update(self):
        self._set_color(self.color)
            
    def _set(self, key, value):
        self.bridge.set_light(self.lid, key, value)

    def _get(self, key):
        return self.bridge.get_light(self.lid, key)
        
    def _on(self):
        self._set('on', True)

    def off(self):
        self._set('on', False)

    def set_color(self, color, brightness=None):
        if color in self.colors:
            if brightness:
                self.set_brightness(brightness)
            else:
                self.set_brightness()
            colorspace = self.colors[color][1]
            value = self.colors[color][0]
            self._set(colorspace, value)
            self.color = color
        else:
            print("WARNING: Unknown color")
            
    def flash(self):
        self._set('alert', 'lselect')

    def set_brightness(self, value=-1): # 0-254
        if value == -1:
            value = self.bri
        elif value > 254:
            value = 254
        if value == 0:
            self.off()
        else:
            self._on()
            self._set('bri', value)
        self.bri = value


class LightController():
    def __init__(self):
        self.lights = []
        
class PhilipsLightController(LightController):
    def __init__(self, ip='192.168.11.111'):
        self.color_converter = Converter()
        self.bridge = self._connect_to_bridge(ip)
        self.lights = self._create_lights(self.bridge)
        
    def _connect_to_bridge(self, ip):
        try:
            b = Bridge(ip)
            b.connect()
        except socket.error as err:
            print("Failed to connect to Philips Hue Bridge @ {ip}: {err}"
                  .format(ip=ip, err=err))
            exit(1)
        return b

    def _create_lights(self, bridge):
        return [Light(bridge, key) for key in bridge.get_light_objects('id').keys()]

    def print_status(self):
        print("{:<6}{:<30}{:<20}".format("Id", "Name", "Reachable"))
        for i, l in enumerate(self.lights):
            print("{:<6}{}".format(i, l))

    def print_connection_status_updates(self):
        for l in self.lights:
            l.print_connection_status_updates()

    def light_from_name(self, name):
        return next((l for l in self.lights if l.name==name), None)


            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bridge_ip", help="ip of the Philips Hue Bridge")
    parser.add_argument("light", help="Light id or name", default=None, type=str, nargs='?')
    parser.add_argument("--set_name", type=str, help="Rename light")
    args = parser.parse_args()

    c = PhilipsLightController(args.bridge_ip)

    if args.light:
        try:
            light = c.lights[int(args.light)]
        except (TypeError, IndexError, ValueError):
            light = c.light_from_name(args.light)
            if not light:
                parser.error("light '{}' not found.".format(args.light))

        if args.set_name:
            light.name = args.set_name

    # Print status if no other cmd is given
    if not args.set_name:
        c.print_status()
