import datetime
from light import Light

class Alert():
    def __init__(self, lights, jobs, allow_nr_failed_jobs=0):
        self.name = ",".join([job.name for job in jobs])
        self.jobs = jobs
        self.lights = lights
        self.last_status = None
        self.first_update = True
        self._allow_nr_failed_jobs = allow_nr_failed_jobs
        
    def __str__(self):
        jobs = ",".join([job.name for job in self.jobs])
        lights = ",".join([light.name for light in self.lights])
        return "Alert: {lights} is showing status from {numjobs} jobs allowing {fails} fails".format(
            numjobs=len(self.jobs), lights=lights, fails=self._allow_nr_failed_jobs)

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
            lights = ",".join([light.name for light in self.lights])
            print("{}: {} is now {}".format(timestamp, lights, color))

            if not self._all_failures_claimed():
                print("Non claimed failed jobs: {}".format(",".join([job.name for job in self._all_non_claimed_failed_jobs()])))

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
        return list(filter(lambda j : not j.ok(allow_nr_failed_jobs=self._allow_nr_failed_jobs), self.jobs))
    
    def _all_failures_claimed(self):
        return not self._all_non_claimed_failed_jobs()

    def _all_non_claimed_failed_jobs(self):
        return list(filter(lambda job : not job.claimed, self._failed_jobs()))
