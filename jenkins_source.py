import ast
from urllib import request

class JenkinsJob():

    def __init__(self, url, name=None,
                 allow_nr_failed_jobs=0,
                 ignore_never_successful=True):
        self._name = name
        self.url = url
        self._allowed_fails = allow_nr_failed_jobs
        self._ignore_never_successful = ignore_never_successful

    def __str__(self):
        return self.name

    @property
    def name(self):
        if not self._name:
            data = _fetch_data(self.url)
            self._name = data['name']
        return self._name
        
    @property
    def ok(self):
        return self._ok

    @property
    def last_ok(self):
        return self._last_ok
        
    @property
    def claimed(self):
        return self._claimed

    def update(self):
        data = _fetch_data(self.url)

        if not data['builds']:
            self._ok = True
            self._last_ok = True
            self._claimed = False
            return

        last_build_url = data['lastCompletedBuild']['url']
        last_build = _fetch_data(last_build_url)
        self._claimed = any([action.get('claimed', False) for action in last_build['actions']])

        last_build_nr = last_build['number']
        try:
            last_failed_build_nr = data['lastFailedBuild']['number']
        except (KeyError, TypeError):
            last_failed_build_nr = None

        try:
            last_successful_build_nr = data['lastSuccessfulBuild']['number']
        except (KeyError, TypeError):
            last_successful_build_nr = None

        # For now, ignore all jobs without a last successful build 
        self._ok = ((not last_failed_build_nr and self._ignore_never_successful) or
                    (last_failed_build_nr and last_successful_build_nr and
                     (last_successful_build_nr + self._allowed_fails >= last_failed_build_nr)))
        self._last_ok = last_build_nr == last_successful_build_nr

        if not self._ok:
            try:
                print('Failed {} nr times {}'.format(
                      self.url, last_failed_build_nr - last_successful_build_nr))
            except TypeError:
                print('Failed {}'.format(self.url))

class JenkinsView():

    def __init__(self, url, name=None, allow_nr_failed_jobs=0):
        self.url = url
        self._name = name
        self._allowed_fails = allow_nr_failed_jobs

    @property
    def name(self):
        if not self._name:
            data = _fetch_data(self.url)
            try:
                self._name = data['name']
            except KeyError:
                self._name = ""
        return self._name

    @property
    def ok(self):
        return all(job.ok for job in self._jobs)

    @property
    def last_ok(self):
        return all(job.last_ok for job in self._jobs)

    @property
    def claimed(self):
        return (any(job.claimed for job in self._jobs) and
                all(job.ok or job.claimed for job in self._jobs))

    def update(self):
        try:
            for job in self._jobs:
                job.update()
        except AttributeError:
            for job in self.jobs:
                job.update()

    @property
    def children(self):
        return self.jobs + self.views

    @property
    def jobs(self):
        data = _fetch_data(self.url)
        try:
            self._jobs = [JenkinsJob(job['url'], job['name'])
                          for job in data['jobs']]
        except KeyError:
            print("WARNING: Cannot parse view")
            self._jobs = []
        print("View {} has {} jobs".format(self.name, len(self._jobs)))

        return self._jobs

    @property
    def views(self):
        data = _fetch_data(self.url)
        try:
            return [JenkinsView(job['url'], job['name'])
                    for job in data['views']]
        except KeyError:
            print("WARNING: Cannot parse view")
            return []


def _print_job(job):
    print("{:<30} {:<6} {} ".format(
        job['name'], job['color'], job['url']))

def print_all_jobs(url):
    data = jenkins_get(url)
    if 'jobs' in data:
        for job in data['jobs']:
            _print_job(job)
    else:
        _print_job(data)

def _get_all_jobs(url):
    data = jenkins_get(url)
    if 'jobs' in data:
        return [job for job in data['jobs']]
    else:
        return [data]

def _get_jenkins_jobs(url, job_names=None):
    return [Job(job) for job in _get_all_jobs(url)]

def _fetch_data(url):
    x = request.urlopen(url + "/api/python")
    y = x.read().decode("utf-8")
    return ast.literal_eval(y)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jenkins", help="url of a jenkins server")
    args = parser.parse_args()
    print_all_jobs(args.url)
