from phue import Bridge, PhueRegistrationException
from rgb_cie import Converter
import datetime
import socket
import argparse

class Light():
    def __init__(self, associated_bridge, bridge_light_id):
        self._bridge = associated_bridge
        self.lid = bridge_light_id
        self._name = self._get('name')
        self._create_colors()
        self._color = None
        self._brightness = self._get('bri')
        self._reachable = None
        self._on = self._get('on')
        
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
        return "{:<30}{:<20}".format(self.name, "yes" if self.reachable else "no")
    
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._set('name', value)
        self._name = self._get('name')
        if self._name != value:
            print("ERROR: Failed to set name")

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        if color in self.colors:
            colorspace = self.colors[color][1]
            value = self.colors[color][0]
            self._set(colorspace, value)
            self._color = color
        else:
            print("ERROR: Unknown color")

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value): # 0-254
        if value > 254:
            value = 254
        self._brightness = value
        self._set('on', (value > 0))
        if self.on:
            # brightness cannot be set when light is turned off
            self._set('bri', value)

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        self._on = value
        if value:
            self._set('on', True)
            self.brightness = self._brightness
        else:
            self._set('on', False)
        
    @property
    def reachable(self):
        return self._bridge.get_light(self.lid, 'reachable')

    def print_connection_status_updates(self):
        reachable = self.reachable
        if self._reachable != reachable:
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M")
            self._reachable = reachable
            name = self._bridge.get_light(self.lid, 'name')
            print("{}: {} is now {}".format(
                  timestamp, name, "reachable" if reachable else "out of range"))

    def _set(self, key, value):
        self._bridge.set_light(self.lid, key, value)

    def _get(self, key):
        return self._bridge.get_light(self.lid, key)
        
    def flash(self):
        self._set('alert', 'lselect')



class LightController():
    def __init__(self):
        self.lights = []
        
class HueLightController(LightController):
    def __init__(self, ip):
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
        except PhueRegistrationException:
            print("Press link button on Philips Hue Bridge and rerun within 30 sec")
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

    def remove_light(self, light):
        address = '/api/' + self.bridge.username + '/lights/' + str(light.lid)
        result = self.bridge.request(mode='DELETE', address=address)
        if not 'success' in result[0]:
            print("Failed to remove light")

    def start_search_for_new_lights(self):
        address = '/api/' + self.bridge.username + '/lights'
        result = self.bridge.request(mode='POST', address=address)
        if 'success' in result[0]:
            print("Search started")
        else:
            print("Failed to start search")

    # Undocumented way of stealing lights from another bridge.
    # The lights must be close to the bridge for this to work.
    def touch_link(self):
        address = '/api/' + self.bridge.username + '/config'
        data = '{"touchlink":true}'
        result = self.bridge.request('PUT', address, data)


def get_light(parser, ctrl, id_or_name):
    try:
        return ctrl.lights[int(id_or_name)]
    except (TypeError, IndexError, ValueError):
        light = ctrl.light_from_name(id_or_name)
        if light:
            return light
        parser.error("light '{}' not found.".format(id_or_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bridge_ip", help="ip of the Philips Hue Bridge")
    parser.add_argument("light", help="Light ids or names", default=[], type=str, nargs='*')
    parser.add_argument("--rename", type=str, help="Rename light")
    parser.add_argument("--flash", action="store_true", help="Flash light(s) for 15 sec")
    parser.add_argument("--find-new-lights", action="store_true", help="Start a search for new lights")
    parser.add_argument("--remove", action="store_true", help="Remove light from bridge")
    parser.add_argument("--steal", action="store_true", help="Steal nearby lights bound to another bridge")
    
    args = parser.parse_args()

    c = HueLightController(args.bridge_ip)
    lights = [get_light(parser, c, light) for light in args.light]

    if not lights:
        if args.rename or args.flash:
            parser.error("missing argument: light")

        c.print_status()

    if args.find_new_lights:
        c.start_search_for_new_lights()

    if args.steal:
        c.touch_link()

    for light in lights:
        if args.rename:
            light.name = args.rename

        if args.flash:
            light.flash()

        if args.remove:
            c.remove_light(light)
