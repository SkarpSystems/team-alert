import ast
from urllib import request

class Job():
    def __init__(self, url_data):
        self.name = url_data['name']
        self.url = url_data['url']

    def __str__(self):
        return self.name
        
    def update(self):
        url_data = jenkins_get(self.url)
        self.color = url_data['color']
        last_build = jenkins_get(url_data['lastBuild']['url'])
        self.claimed = any([action.get('claimed', False) for action in last_build['actions']])
        
    def ok(self):
        return self.color == 'blue'

    def is_claimed(self):
        return self.claimed

    
def jenkins_get(url):
    x = request.urlopen(url + "/api/python")
    y = x.read().decode("utf-8")
    return ast.literal_eval(y)    

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

def get_jenkins_jobs(url, job_names=None):
    return [Job(job) for job in _get_all_jobs(url)]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jenkins", help="url of a jenkins server")
    args = parser.parse_args()
    print_all_jobs(args.url)
