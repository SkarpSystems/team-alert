import datetime

class Alert():
    def __init__(self, lights, jobs):
        self.name = ",".join([job.name for job in jobs])
        self.jobs = jobs
        self.lights = lights
        self.last_status = None
        self.first_update = True
        
    def __str__(self):
        jobs = ",".join([job.name for job in self.jobs])
        lights = ",".join([light.name for light in self.lights])
        return "Alert: {lights} is showing status from {jobs}".format(jobs=jobs, lights=lights)

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
        return not self._failed_jobs()

    def _failed_jobs(self):
        return list(filter(lambda j : not j.ok, self.jobs))
    
    def _all_failures_claimed(self):
        return all([job.claimed for job in self._failed_jobs()])

def _light_from_name(lights, name):
    return next((l for l in lights if l.name==name), None)
    
def create_alerts(alert_cfg, lights, jobs):
    alerts = []
    jobs_by_name = {job.name: job for job in jobs}
    for cfg in alert_cfg:
        job_names_to_watch = cfg['jobs_to_watch']
        try:
            monitored_jobs = [jobs_by_name[name] for name in job_names_to_watch]
        except KeyError:
            # Failed to find all jobs specified in cfg
            pass
        else:
            light = _light_from_name(lights, cfg['light'])
            if not light:
                print("Configured light {} does not exists on hue bridge {}".format(
                    cfg['light'], args.huebridge))
                exit(1)
            alerts.append(Alert([light], monitored_jobs))
    return alerts
