from jenkins_source import get_jenkins_jobs
from alert import create_alerts
from hue_light import HueLightController
from light import Light
from time import sleep
import json
from jsonschema import validate, ValidationError
import datetime
import syslog
import argparse
            
def light_from_name(lights, name):
    return next((l for l in lights if l.name==name), None)

def read_config(cfg_file_name):
    with open('alerts_cfg.schema.json') as schema_file:
        schema = json.load(schema_file)
    try:
        with open(cfg_file_name) as cfg_file:
            config = json.load(cfg_file)
        validate(config, schema)
    except:
        print("Error when reading config file {}".format(cfg_file_name))
        raise
    else:
        if 'virtual_lights' not in config:
            config['virtual_lights'] = []
        return config
    exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("alerts_cfg",type=str, help="Json configuration file")
parser.add_argument("huebridge", help="ip of the Philips Hue Bridge")
parser.add_argument("jenkins", help="url of a jenkins server")
parser.add_argument("--poll_rate", default=10, type=int, help="seconds delay between each update")
args = parser.parse_args()

syslog.syslog('team-alert initializing...')

cfg = read_config(args.alerts_cfg)
hue_controller = HueLightController(args.huebridge)
virtual_lights = [Light(**args) for args in cfg['virtual_lights']]
lights = hue_controller.lights + virtual_lights
jobs = get_jenkins_jobs(args.jenkins)
visualizations = create_alerts(cfg['alerts'], lights, jobs)

syslog.syslog('lightctrl starting update loop')

print("Updating status every {} sek".format(args.poll_rate))
while True:
    for v in visualizations:
        v.update()
    hue_controller.print_connection_status_updates()
    sleep(args.poll_rate)

        

