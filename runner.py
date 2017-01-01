from jenkins_source import get_jenkins_jobs
from alert import create_alerts
from hue_light import HueLightController
from light import Light
import json
from jsonschema import validate, ValidationError


class Runner():
    def __init__(self, cfg, hue_bridge, jenkins):
        self._hue_bridge_ip = hue_bridge
        self._jenkins_ip = jenkins
        self._cfg_path = cfg
        self.restart()

    def restart(self):
        self._load_config(self._cfg_path)
        hue_controller = HueLightController(self._hue_bridge_ip)
        virtual_lights = [Light(**args) for args in self.cfg['virtual_lights']]
        lights = hue_controller.lights + virtual_lights
        jobs = get_jenkins_jobs(self._jenkins_ip)
        self.alerts = create_alerts(self.cfg['alerts'], lights, jobs)

    def update_alerts(self):
        for alert in self.alerts:
            alert.update()

    def _load_config(self, cfg_file_name):
        with open('alerts_cfg.schema.json') as schema_file:
            schema = json.load(schema_file)
        try:
            with open(cfg_file_name) as cfg_file:
                config = json.load(cfg_file)
            validate(config, schema)
        except:
            print("--- Error when reading config file {} ---".format(cfg_file_name))
            raise
        else:
            if 'virtual_lights' not in config:
                config['virtual_lights'] = []
            self.cfg = config
