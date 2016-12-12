from jenkins_source import get_jenkins_jobs
from hue_light import HueLightController
from time import sleep
import datetime
import syslog
import argparse
from config import configs

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
            light.set_color(color)
            light.set_brightness(brightness)
        
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

    
parser = argparse.ArgumentParser()
parser.add_argument("huebridge", help="ip of the Philips Hue Bridge")
parser.add_argument("jenkins", help="url of a jenkins server")
parser.add_argument("--poll_rate", default=10, type=int, help="seconds delay between each update")
args = parser.parse_args()

syslog.syslog('team-alert initializing...')

c = HueLightController(args.huebridge)
jobs = get_jenkins_jobs(args.jenkins)

visualizations = []
for cfg in configs:
    monitored_jobs = [job for job in jobs if job.name in cfg['jobs_to_watch']]
    light = c.light_from_name(cfg['light'])
    if not light:
        print("Configured light {} does not exists on hue bridge {}".format(
            cfg['light'], args.huebridge))
        exit(1)
    visualizations.append(Visualization([light], monitored_jobs))

for v in visualizations:
    print(v)

syslog.syslog('lightctrl starting update loop')
print("Updating status every {} sek".format(args.poll_rate))
while True:
    for v in visualizations:
        v.update()
    c.print_connection_status_updates()
    sleep(args.poll_rate)

        

