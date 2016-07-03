import os
import re
import subprocess

# github access token to set commit status
# fill in here or create token.txt with it
token  = ""
if os.path.isfile('token.txt'):
    token = open('token.txt').read().replace("\n","")

# context for status updates inside github. needs to be unique, 'default' is okay
# if you only have one ci job running. Use an empty string to disable setting the
# commit status.
github_context = "aspect-8.4.1"

# directory where the local checkout of the git repo sits
repodir = os.getcwd()+"/aspect"

# name of the user/organization on github
github_user = "geodynamics"

# name of the repo on github
github_repo = "aspect"

# command to execute
def execute_test(sha1, name):
    #try:
    cmd = "rm -rf logs/{0};mkdir logs/{0};true".format(sha1)
    answer = subprocess.check_output(cmd,
                                     shell=True,stderr=subprocess.STDOUT)

    #cmd = 'docker run --rm=true ' \
    cmd = './docker_with_timeout.sh 30m ' \
          '--net none ' \
          '-e hash={0} ' \
          '-e name={1} ' \
          '-e BUILDS=\'clang\' ' \
          '-v "$(pwd)/aspect:/source:ro" ' \
          '-v "$(pwd)/logs/{0}:/home/bob/log" ' \
          'tjhei/aspect-tester-8.4.1'.format(sha1, name)
    print "cmd:",cmd
    try:
        answer = subprocess.check_output(cmd,
                                         shell=True,stderr=subprocess.STDOUT)
        print "check output okay"
        return [True, answer]
    except subprocess.CalledProcessError, e:
        print "check output not okay"
        answer = e.output
        print answer
        print "command failed with code", e.returncode
        return [False, answer]
    #except:
    #    return "failed"


# number of tests to go back in time when doing "run-all" default 10
n_old_tests = 2

# if a user that is_allowed() posts a comment that has
# has_hotword(text) return True, the PR is tested
def has_hotword(text):
    if "/run-tests" in text:
        return True
    return False

# return true if user is trusted
def is_allowed(username):
    trusted = ['tjhei', 'bangerth', 'jdannberg', 'gassmoeller', 'ian-r-rose']

    if username in trusted:
        return True
    
    return False

# make a nice link for a test result:
def make_link(sha):
    return "http://www.math.clemson.edu/~heister/cib/aspect-8.4.1/{}/".format(sha)


# for a given line l of the test output return
# "good", "bad", or "neutral"
def status_of_output_line(l):
    status = "neutral"
    if re.match(r'^([ ]*)0 Compiler errors$', l):
        status = "good"
    elif re.match(r'^([ ]*)(\d+) Compiler errors$', l):
        status = "bad"
    elif re.match(r'^100% tests passed, 0 tests failed out of (\d+)$', l):
        status = "good"
    elif re.match(r'^(\d+)% tests passed, (\d+) tests failed out of (\d+)$', l):
        status = "bad"
    elif re.match(r'.*FAILED', l):
        status = "bad"
    return status
