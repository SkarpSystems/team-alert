# team-alert
Team-alert collects status from jenkins jobs and uses this to control Philips Hue based lamps. It can be used to alert software developer teams about failing tests that need attention.

One or more jenkins jobs is set up to control a lamp.

* White light - everything is ok
* Red light - at least one failing job, take action!
* Yellow - all failed jobs have been *claimed* in Jenkins (someone is working on a fix)
* Flashing - The status did just change

Currently there are three usable python modues:

* runner.py - The main program and update loop
* hue_light.py - Interface to Philips Hue Bridge
* jenkins_source.py - Interface to Jenkins
