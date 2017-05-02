import ast
from urllib import request

class Jenkins():

    def __init__(self, url):
        top_data = _fetch_data(url)        
        try:
            self.jobs = { job['name'] : JenkinsJob(job['url']) for job in top_data['jobs'] }
            self.view_urls = { view['name'] : view['url'] for view in top_data['views'] }
        except KeyError:
            print("WARNING: Cannot parse top level jobs")

        print("Jenkins got {} jobs and {} views.".format(len(self.jobs), len(self.view_urls)))

    def get_jobs(self, job_or_view_name):
        if job_or_view_name in self.jobs:
            return [self.jobs[job_or_view_name]]
        elif job_or_view_name in self.view_urls:
            try:
                view_data = _fetch_data(self.view_urls[job_or_view_name])
                return [self.jobs[job['name']] for job in view_data['jobs']]
            except KeyError:
                print("ERROR: Missing job needed by view {}".format(job_or_view_name))
                return []
        else:
            print("ERROR: Cannot find {} on Jenkins".format(job_or_view_name))
            return []

class JenkinsJob():

    def __init__(self, url, name=None,
                 ignore_never_successful=True):
        self._name = name
        self.url = url
        self._ignore_never_successful = ignore_never_successful

    def __str__(self):
        return self.name

    @property
    def name(self):
        if not self._name:
            data = _fetch_data(self.url)
            self._name = data['name']
        return self._name
        
    def ok(self, allow_nr_failed_jobs=0):
        return self.last_ok or (self.nr_times_same_state <= allow_nr_failed_jobs)

    @property
    def nr_times_same_state(self):
        if self._last_failed_build_nr and self._last_successful_build_nr:
            return abs(self._last_failed_build_nr - self._last_successful_build_nr)
        elif (self._last_failed_build_nr and self._oldest_build_nr):
           return self._last_failed_build_nr - self._oldest_build_nr
        elif (self._last_failed_build_nr and self._oldest_build_nr):
           return self._last_successful_build_nr - self._oldest_build_nr
        else:
            return 0

    @property
    def last_ok(self):
        return self._last_build_nr == self._last_successful_build_nr
        
    @property
    def claimed(self):
        return self._claimed
    
    def update(self):
        data = _fetch_data(self.url)

        self._oldest_build_nr = None
        self._last_build_nr = None
        self._last_failed_build_nr = None
        self._last_successful_build_nr = None
        self._claimed = False
        
        if 'builds' not in data or not data['builds'] or \
           'lastSuccessfulBuild' not in data or \
           'lastFailedBuild' not in data or \
           'lastCompletedBuild' not in data:
            print("Missing data in jenkins job api")
            return

        self._oldest_build_nr = min([int(build['number']) for build in data['builds']])
        last_completed_build = _fetch_data(data['lastCompletedBuild']['url'])
        self._claimed = any([action.get('claimed', False) for action in last_completed_build['actions']])
        self._last_build_nr = last_completed_build['number']

        if data['lastFailedBuild']:
            self._last_failed_build_nr = data['lastFailedBuild'].get('number', None)
        if data['lastSuccessfulBuild']:
            self._last_successful_build_nr = data['lastSuccessfulBuild'].get('number', None)

        if not self.ok:
            try:
                print('Failed {} nr times {}'.format(
                      self.url, self.nr_times_same_state))
            except TypeError:
                print('Failed {}'.format(self.url))


def _fetch_data(url, tries=10):
    for i in range(1, tries+1):
        try:
            x = request.urlopen(url + "/api/python", timeout=10)
            y = x.read().decode("utf-8")
            break
        except:
            print("Failed to fetch {} (try {}/{})".format(url, i, tries))
            if i >= tries:
                exit(1)
    return ast.literal_eval(y)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jenkins", help="url of a jenkins server")
    args = parser.parse_args()
    print_all_jobs(args.url)
