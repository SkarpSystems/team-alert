from jenkins_source import get_jenkins_jobs
from light import Light
from hue_light import HueLightController
from time import sleep
import datetime
import syslog
import argparse
from config import configs, virtual_lights

class Visualization():
    def __init__(self, lights, jobs):
        self.name = ",".join([job.name for job in jobs])
        self.jobs = jobs
        self.lights = lights
        self.last_status = None
        self.first_update = True
        
    def __str__(self):
        jobs = ",".join([job.name for job in self.jobs])
        lights = ",".join([light.name for light in self.lights])
        return "Visual: {lights} --> {jobs}".format(jobs=jobs, lights=lights)

    def update(self):
        for job in self.jobs:
            job.update()
        ok = self._ok()
        
        if ok:
            color = 'white'
            brightness = 180
        else:
            color = 'red'
            brightness = 240
            if self._all_failures_claimed():
                color = 'orange'

        self._set_lights_output(color, brightness)
        if self._has_changed((ok, color)):
            if not self.first_update:
                self._do_flash()

            # print status to terminal on change
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M")
            print("{}: {} is now {}".format(timestamp, self.name, color))

        self.first_update = False

    def _set_lights_output(self, color, brightness):
        for light in self.lights:
            light.color = color
            light.brightness = brightness
        
    def _do_flash(self):
        for light in self.lights:
            light.flash()
            
    def _has_changed(self, a_hash):
        changed = self.last_status != a_hash
        self.last_status = a_hash
        return changed
            
    def _ok(self):
        #print('failed_jobs', self._failed_jobs())
        return not self._failed_jobs()

    def _failed_jobs(self):
        return list(filter(lambda j : not j.ok(), self.jobs))
    
    def _all_failures_claimed(self):
        return all([job.is_claimed() for job in self._failed_jobs()])
            
def light_from_name(lights, name):
    return next((l for l in lights if l.name==name), None)

def create_visualizations(configs, lights, jobs):
    visualizations = []
    jobs_by_name = {job.name: job for job in jobs}
    for cfg in configs:
        job_names_to_watch = cfg['jobs_to_watch']
        try:
            monitored_jobs = [jobs_by_name[name] for name in job_names_to_watch]
        except KeyError:
            # Failed to find all jobs specified in cfg
            pass
        else:
            light = light_from_name(lights, cfg['light'])
            if not light:
                print("Configured light {} does not exists on hue bridge {}".format(
                    cfg['light'], args.huebridge))
                exit(1)
            visualizations.append(Visualization([light], monitored_jobs))
    return visualizations 

    
parser = argparse.ArgumentParser()
parser.add_argument("huebridge", help="ip of the Philips Hue Bridge")
parser.add_argument("jenkins", help="url of a jenkins server")
parser.add_argument("--poll_rate", default=10, type=int, help="seconds delay between each update")
args = parser.parse_args()

syslog.syslog('team-alert initializing...')

hue_controller = HueLightController(args.huebridge)
virtual_lights = [Light(**args) for args in virtual_lights]
lights = hue_controller.lights + virtual_lights
jobs = get_jenkins_jobs(args.jenkins)


visualizations = create_visualizations(configs, lights, jobs)
for v in visualizations:
    print(v)

syslog.syslog('lightctrl starting update loop')
print("Updating status every {} sek".format(args.poll_rate))
while True:
    for v in visualizations:
        v.update()
    hue_controller.print_connection_status_updates()
    sleep(args.poll_rate)

        

