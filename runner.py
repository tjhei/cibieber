# timo.heister@gmail.com

# project configuration is in config.py

import random
import re
import os
import sys
import subprocess
import json as js
from datetime import datetime
import urllib2

from config import *

color_green = "#99ff99"
color_red = "#ff0000"


def github_read(token, url):
    #print "read: ", url
    req = urllib2.Request(url)
    if token!="":
        req.add_header("Authorization", "token {0}".format(token))
    res = urllib2.urlopen(req)
    result = res.read()
    return result
    #except urllib2.HTTPError as e:
    #    print "setting github status failed: HTTP error ", e.code
    #except urllib2.URLError as e:
    #    print "setting github status failed: failure ", e.reason
    #return ""
     

def github_set_commit_status(user, repo, token, sha1, state="success", description="", link=""):
    #pending, success, error, failure

    description = description[0:min(len(description),140)] #github doesn't like too long description

    if github_context=="" or token=="":
        return

    data = js.dumps({'state' : state, 'context' : github_context, 'description' : description, 'target_url' : link})
    url = "https://api.github.com/repos/{0}/{1}/statuses/{2}".format(github_user, github_repo, sha1)

    req = urllib2.Request(url)
    req.add_header("Authorization", "token {0}".format(token))
    req.add_data(data)
    result = ""
    try:
        res = urllib2.urlopen(req)
        result = res.read()
    except urllib2.HTTPError as e:
        print "setting github status failed: HTTP error ", e.code, e.reason, url, data 
    except urllib2.URLError as e:
        print "setting github status failed: failure ", e.reason, result

def date_to_epoch(dt):
    epoch = datetime.utcfromtimestamp(0)
    return (dt-epoch).total_seconds()

def epoch_to_date(seconds):
    return datetime.utcfromtimestamp(seconds)

def text_to_html(text):
    import re
    lines = text.split("\n")
    outlines = []
    for l in lines:
        status = status_of_output_line(l)
        assert(status in ["good", "bad", "neutral"])
            
        if status=="good":
            outlines.append("<p style='background-color:{0}'>{1}</p>".format(color_green, l.encode("utf-8")))
        elif status=="bad":
            outlines.append("<p style='background-color:{0}'>{1}</p>".format(color_red, l.encode("utf-8")))
        else:
            outlines.append("{0}<br/>".format(l.encode("utf-8")))
    
    return "".join(outlines)


class history:
    def __init__(self):
        # entry with sha1 as key
        # entry is dict() with "sha1", "time", "text", "good", "name"
        self.data = dict()
        self.dbname = "test.db"
        self.timeformat = "%Y-%m-%d %H:%M:%S"

    def load(self):
        try:
            f = open(self.dbname, 'r')
        except IOError:
            self.save()
            return

        text = f.read()
        f.close()
        self.data = js.loads(text)
        #print "loading {0} entries...".format(len(self.data))

    def save(self):
        text = js.dumps(self.data)
        #print "saving {0} entries...".format(len(self.data))
        f = open(self.dbname, 'w')
        f.write(text)
        f.close()

    def sort_keys(self):
        keys = []
        for x in self.data.values():
            keys.append((x['sha1'], x['time']))
        
        return [ k[0] for k in sorted(keys, key=lambda x: x[1], reverse=True) ]

    def dump(self):
        print "dumping {0} entries".format(len(self.data))

        sorted_keys = self.sort_keys()

        print "SHA1 time good name:"
        for sha in sorted_keys:
            x = self.data[sha]
            timestr = "?"
            try:
                dt = epoch_to_date(x['time'])
                timestr = dt.strftime(self.timeformat)
            except:
                pass
            print "{} {} {} {}".format(x['sha1'], timestr, x['good'], x['name'])
    
    def render(self):
        f = open ("results.html", "w")

        f.write("<html><body><h1>Test Results</h1>\n")
        f.write("<p>Last update: {0}</p>".format(datetime.now().strftime(self.timeformat)))

        f.write("<script>function toggle(id) {var o = document.getElementById(id);if (o.style.display=='none') o.style.display='table-row'; else o.style.display='none'; }</script>\n")
        f.write("<table border=1 width='100%' style='border-collapse:collapse'>\n")
        
        sorted_keys = self.sort_keys()

        f.write("<tr><td width='1%'>SHA1</td><td>PASS</td><td>Time</td><td>Comment</td><td>Details</td></tr>\n")
        for sha in sorted_keys:
            x = self.data[sha]
            timestr = "?"
            try:
                dt = epoch_to_date(x['time'])
                timestr = dt.strftime(self.timeformat)
            except:
                pass
            
            sha1 = x['sha1'].replace("\n","n")
            details = "<a href='#' onclick='toggle(\"sha{0}\")'>click</a>".format(sha1)
            if x['good']:
                passtxt = "<p style='background-color:#99ff99'>{0}</p>".format("true")
            else:
                passtxt = "<p style='background-color:#ff0000'>{0}</p>".format("false")
            name = x['name']
            f.write("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>\n".format(
                    sha1[0:10], passtxt, timestr, name, details))
            text = text_to_html(x['text'])
            f.write("<tr id='sha{0}' style='display: none'><td colspan='6'><a href='{2}'>{0}</a><br/>{1}</td></tr>\n".format(sha1, text, make_link(sha1)))

        f.write("</table>\n")

        f.write("</body></html>")

        f.close()

    def have(self, sha):
        return sha in self.data.keys()

    def delete(self, sha):
        if sha in self.data.keys():
            self.data.pop(sha)
            return

        count = 0
        for k in self.data.keys():
            if k.startswith(sha):
                count = count + 1

        if count==0:
            print "ERROR: sha1 not found."
        elif count==1:
            for k in self.data.keys():
                if k.startswith(sha):
                    self.data.pop(k)
                    print "1 test result deleted"
                    return
        else:
            print "ERROR: sha1 is not unique."
            

    def add(self, sha, good, name, text):
        time = date_to_epoch(datetime.now())

        e = dict(sha1=sha, time=time, name=name, good=good, text=text)
        self.data[sha] = e


def is_successful(lines):
    good = True
    for l in lines:
        status = status_of_output_line(l)
        if status=="bad":
            good = False

    return good


def test(repodir, h, name=""):
    sha1 = subprocess.check_output("cd {0};git rev-parse HEAD".format(repodir),
                                   shell=True).replace("\n","")
    print "running", sha1

    if len(name)>0:
        name = "-"+name.replace("/","_").replace(":","_")

    answer = ""
    try:
        ok,answer = execute_test(sha1, name)
        good = ok and is_successful(answer.split("\n"))
    except:
        good = False

    print good
    h.add(sha1, good, name, answer)
    h.save()
    return good


whattodo = ""

if len(sys.argv)<2:
    print "gitautotester"
    print "-------------"
    print ""
    print "usage:"
    print "runner.py do-current\n\t\t tests the current revision in this directory"
    print "runner.py run-all\n\t\t runs all revisions on master not tested"
    print "runner.py do-pullrequests\n\t\t test all open PRs that are okay to be tested"
    print "runner.py mark-pullrequests\n\t\t mark all open PRs as pending on github"
    print ""
    print "runner.py newdb\n\t\t creates a new database overwriting the existing one"
    print "runner.py dump\n\t\t lists entry in the current database"
    print "runner.py testdata\n\t\t puts some test data into the database"
    print "runner.py pullrequests\n\t\t lists the open pull requests"
    print "runner.py test <user>/<repo>:<ref>\n\t\t tests the branch ref from user/repo on github"
    print "runner.py delete <sha1>\n\t\t deletes the sha1 from the database (fuzzy matching)"
    print "runner.py render\n\t\t generate results.html"
else:
    whattodo = sys.argv[1]
    arg1 = ""
    if len(sys.argv)>2:
        arg1 = sys.argv[2]

if whattodo=="newdb":
    h = history()
    h.save()

if whattodo != "":
    h = history()
    h.load()

if whattodo == "dump":
    h.dump()

if whattodo == "testdata":    
    h.add("r"+str(random.randrange(10000,99999)), True, "test", "this is some text")
    h.save()
    
if whattodo == "delete":
    h.delete(arg1)
    h.save()

if whattodo == "run-all":
    ret = subprocess.check_call("cd {0} && git reset --hard -q && git clean -fd -q".format(repodir), shell=True)
    ret = subprocess.check_call("cd {0} && git checkout master -q".format(repodir), shell=True)
    
    try:
        ret = subprocess.check_output("cd {0} && git pull origin -q".format(repodir), shell=True)
    except subprocess.CalledProcessError:
        print "pull failed, ignoring"

    answer = subprocess.check_output("cd {0} && git log --format=oneline --first-parent -n {1}".format(repodir, n_old_tests),
                                     shell=True,stderr=subprocess.STDOUT)
    lines = answer.split("\n")
    for l in lines[::-1]:
        sha1 = l.split(" ")[0]
        if len(sha1)!=40:
            continue
        if not h.have(sha1):
            print "testing {}".format(sha1)
            
            ret = subprocess.check_call("cd {0} && git checkout {1} -q".format(repodir, sha1),
                                        shell=True)

            ret = subprocess.check_call("cd {0} && git reset --hard -q && git clean -fd -q".format(repodir), shell=True)
            test(repodir, h, "")
        
        else:
            print "skipping {}".format(sha1)
            result = h.data[sha1]
            print "  ", result['good'], result['name']#, result['text']


    ret = subprocess.check_call("cd {0} && git reset --hard -q && git clean -fd -q".format(repodir), shell=True)
    ret = subprocess.check_call("cd {0} && git checkout master -q".format(repodir), shell=True)

    
if whattodo == "do-current":
    print repodir
    test(repodir, h, "manual")


if whattodo == "pullrequests":
    r = github_read(token, "https://api.github.com/repos/{0}/{1}/pulls".format(github_user, github_repo))
    data = js.loads(r)
    print "found {0} pull requests...".format(len(data))
    for pr in data:
        by = pr['user']['login']
        title = pr['title'].encode("utf-8")
        sha = pr['head']['sha']
        print "PR{}: {} '{}' by {}".format(pr['number'], sha, title, by)
        print "  use: python runner.py test {0}:{1}".format(pr['head']['repo']['full_name'],pr['head']['ref'])
        #print simplejson.dumps(pr, sort_keys=True, indent=4, separators=(',', ': '))
        if h.have(sha):
            print "  already tested"
            result = h.data[sha]
            print "  ", result['good'], result['name'], result['text']
        else:
            allowed = False
            if is_allowed(by):
 #               print "  allowed owner"
                allowed = True
            else:
                r = github_read(token, "https://api.github.com/repos/{0}/{1}/issues/{2}/comments".format(github_user, github_repo, pr['number']))
                comments = js.loads(r)
                for comment in comments:
                    user = comment['user']['login']
                    text = comment['body']
                    if is_allowed(user) and has_hotword(text):
                        #print "  allowed by hotword from ", user
                        allowed = True
            
            if allowed:
                pass
#                print "TODO: testing"
                

if whattodo == "do-pullrequests":
    r = github_read(token, "https://api.github.com/repos/{0}/{1}/pulls".format(github_user, github_repo))
    data = js.loads(r)
    print "found {0} pull requests...".format(len(data))
    for pr in data:
        by = pr['user']['login']
        title = pr['title'].encode("utf-8")
        sha = pr['head']['sha']
        print "PR{}: {} '{}' by {}".format(pr['number'], sha, title, by)
        #print "  use: python runner.py test {0}:{1}".format(pr['head']['repo']['full_name'],pr['head']['ref'])
        #print simplejson.dumps(pr, sort_keys=True, indent=4, separators=(',', ': '))
        if h.have(sha):
            result = h.data[sha]
            print "  already tested: good={} - '{}':".format(result['good'], result['name'])
            print result['text'].encode("utf-8")
        else:
            allowed = False
            if is_allowed(by):
 #               print "  allowed owner"
                allowed = True
            else:
                r = github_read(token, "https://api.github.com/repos/{0}/{1}/issues/{2}/comments".format(github_user, github_repo, pr['number']))
                comments = js.loads(r)
                for comment in comments:
                    user = comment['user']['login']
                    text = comment['body']
                    if is_allowed(user) and has_hotword(text):
                        print "  allowed by hotword from {}".format(user)
                        allowed = True
            
            if allowed:
                print "testing..."
                github_set_commit_status(github_user, github_repo, token, sha, "pending", "tester is running")

                ret = subprocess.check_call("cd {0} && git reset --hard -q && git clean -fd -q".format(repodir), shell=True)
                ret = subprocess.check_call("cd {0} && git fetch https://github.com/{1}/{2} refs/pull/{3}/head -q".format(repodir, github_user, github_repo, pr['number']), shell=True)
                ret = subprocess.check_call("cd {0} && git checkout {1} -q".format(repodir, sha),
                                        shell=True)
                ret = subprocess.check_call("cd {0} && git reset --hard -q && git clean -fd -q".format(repodir), shell=True)
                ret = test(repodir, h, "PR{}".format(pr['number']))
                

                text = h.data[sha]['text']
                link = make_link(sha)

                if ret:
                    github_set_commit_status(github_user, github_repo, token, sha, "success", text, link)
                else:
                    github_set_commit_status(github_user, github_repo, token, sha, "failure", text, link)
                ret = subprocess.check_call("cd {0} && git checkout master -q".format(repodir),
                                        shell=True)

            else:
                print "not allowed! please add a comment containing '/run-tests'"
                                
if whattodo == "mark-pullrequests":
    if github_context=="":
        print " no context given in config.py. Exiting."
        raise RuntimeError()
    if token=="":
        print " no token given in config.py. Exiting."
        raise RuntimeError()

    r = github_read(token, "https://api.github.com/repos/{0}/{1}/pulls".format(github_user, github_repo))
    data = js.loads(r)
    print "found {0} pull requests...".format(len(data))
    for pr in data:
        by = pr['user']['login']
        title = pr['title'].encode("utf-8")
        sha = pr['head']['sha']
        print "PR{}: {} '{}' by {}".format(pr['number'], sha, title, by)
        #print "  use: python runner.py test {0}:{1}".format(pr['head']['repo']['full_name'],pr['head']['ref'])
        #print simplejson.dumps(pr, sort_keys=True, indent=4, separators=(',', ': '))
        if h.have(sha):
            result = h.data[sha]
            print "  already tested: good={} - '{}':".format(result['good'], result['name'])
            #print result['text']
        else:
            allowed = False
            if is_allowed(by):
                allowed = True
            else:
                r = github_read(token, "https://api.github.com/repos/{0}/{1}/issues/{2}/comments".format(github_user, github_repo, pr['number']))
                comments = js.loads(r)
                for comment in comments:
                    user = comment['user']['login']
                    text = comment['body']
                    if is_allowed(user) and has_hotword(text):
                        print "  allowed by hotword from {}".format(user)
                        allowed = True
            statustext="queued..."
            if not allowed:
                statustext="(not allowed)"

            # find status:
            r = github_read(token, "https://api.github.com/repos/{0}/{1}/commits/{2}/statuses".format(github_user, github_repo, sha))
            data = js.loads(r)
            has_status = False
            desc = ""
            for st in data:
                if st['context']==github_context:
                    has_status = True
                    desc = st['description']
            
            if desc in {"", "queued...", "(not allowed)"}:
                if desc==statustext:
                    print "... already got status", statustext
                else:
                    print "... setting status ", statustext
                    github_set_commit_status(github_user, github_repo, token, sha, "pending", statustext)
            else:
                print " has some desc, so skipping: ", desc

if whattodo == "rate":
    r = urllib2.urlopen("https://api.github.com/rate_limit".format()).read()
    print r
                        
     

if whattodo == "test":
    #arg1
    r = re.match("^(\w+)/(\w+):(.+)$", arg1)
    if r:
        user = r.group(1)
        repo = r.group(2)
        ref = r.group(3)
        print user, repo, ref
        
        ret = subprocess.check_call("cd {0} && git fetch https://github.com/{1}/{2} {3} -q".format(repodir, user, repo, ref), shell=True)
        ret = subprocess.check_call("cd {0} && git checkout FETCH_HEAD -q".format(repodir), shell=True)
    
        test(repodir, h, arg1)
    
        ret = subprocess.check_call("cd {0} && git checkout master -q".format(repodir), shell=True)

    
if whattodo =="render":
    h.render()








    


    
