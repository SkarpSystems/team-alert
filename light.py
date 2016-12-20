class Light():
    def __init__(self, name, enable_debug_print=False):
        self._name = name
        self._color = None
        self._brightness = 0
        self._on = False
        self._debug_prints = enable_debug_print

    def __str__(self):
        return "{:<30}".format(self.name)

    @property
    def name(self):
        return self._name

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        if color != self._color:
            self._print("changed color to {}".format(color))
        self._color = color

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        if value != self.brightness:
            self._print("changed brightness to {}".format(value))
        self._brightness = value

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        if value != self._on:
            self._print("turned {}".format('on' if value else 'off'))
        self._on = value

    def flash(self):
        self._print("flashing")

    def _print(self, text):
        if self._debug_prints:
            print("Light '{name}': {text}".format(
                name=self._name, text=text))


class LightController():
    def __init__(self, light_names=[], enable_debug_print=False):
        self.lights = [Light(name, enable_debug_print) for name in light_names]

    def light_from_name(self, name):
        return next((l for l in self.lights if l.name==name), None)
