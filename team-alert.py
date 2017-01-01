import argparse
import sched, time
import syslog
from runner import Runner

class PeriodicScheduler(sched.scheduler):
    def enter_periodic(self, interval, func, initial_delay=None, prio=1):
        args = {'func':func, 'interval':interval, 'prio':prio}
        if initial_delay:
            self.enter(initial_delay, prio, self.enter_periodic, kwargs=args)
        else:
            func()
            self.enter(interval, prio, self.enter_periodic, kwargs=args)


parser = argparse.ArgumentParser()
parser.add_argument("alerts_cfg",type=str, help="Json configuration file")
parser.add_argument("huebridge", help="ip of the Philips Hue Bridge")
parser.add_argument("jenkins", help="url of a jenkins server")
parser.add_argument("--poll_rate", default=10, type=int, help="seconds delay between each update")
parser.add_argument("--cfg_poll_rate", default=3600, type=int, help="seconds delay between each refresh off the config file")
args = parser.parse_args()

syslog.syslog('team-alert initializing...')
runner = Runner(args.alerts_cfg, args.huebridge, args.jenkins)
            
print("Updating status every {} sek".format(args.poll_rate))
scheduler = PeriodicScheduler(time.time, time.sleep)
scheduler.enter_periodic(args.cfg_poll_rate, runner.restart, args.cfg_poll_rate)
scheduler.enter_periodic(args.poll_rate, runner.update_alerts)
scheduler.run()
