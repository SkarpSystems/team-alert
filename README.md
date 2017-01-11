# team-alert
Team-alert collects status from jenkins jobs and uses this to control Philips Hue based lamps. It can be used to alert software developer teams about failing tests that need attention.

One or more jenkins jobs is set up to control a lamp.

* White light - everything is ok
* Red light - at least one failing job, take action!
* Yellow - all failed jobs have been *claimed* in Jenkins (someone is working on a fix)
* Flashing - The status did just change

Currently there are two python modules that can be used from command line:

* team-alert.py - The main program and update loop scheduling
* hue_light.py - Interface to Philips Hue Bridge

A configuration file sample is available as alerts_cfg_sample.json. It defines the mapping between lamps and jenkins jobs.
