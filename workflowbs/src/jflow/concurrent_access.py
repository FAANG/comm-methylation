#
# Copyright (C) 2015 INRA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
__license__ = 'GNU General Public License'
__version__ = '0.2.0'

import os
import re
import time
import json
import random


def priority_compare_key(cmp_func):
    """
    @summary: Converts a cmp= function into a key= function (python 2.x to 3.x).
    """
    class K:
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return cmp_func(self.obj, other.obj) < 0
        def __gt__(self, other):
            return cmp_func(self.obj, other.obj) > 0
        def __eq__(self, other):
            return cmp_func(self.obj, other.obj) == 0
        def __le__(self, other):
            return cmp_func(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return cmp_func(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return cmp_func(self.obj, other.obj) != 0
    return K

def priority_compare( a, b ):
    """
    @summary: The comparison rules to establish the priorities between two
    requests.
    """
    compare = -1 # By default a is the first
    if b['timestamp'] < a['timestamp']:
        compare = 1
    elif b['timestamp'] == a['timestamp']:
        if b['PID'] < a['PID']:
            compare = 1
        elif b['PID'] == a['PID']:
            if b['random'] < a['random']:
                compare = 1
    return compare

def get_priority( requests, evaluated_request ):
    """
    @summary: Returns the access priority for the evaluated request.
    @param requests: [list] The list of all access requests.
    @param evaluated_request: [dict] The evaluated access request.
    @return: [int] The access priority for the evaluated request. the maximum
                   priority is 1.
    """
    priority = None
    requests.sort( key=priority_compare_key(priority_compare) )
    for idx, current_request in enumerate(requests):
        if current_request['timestamp'] == evaluated_request['timestamp'] and current_request['PID'] == evaluated_request['PID'] and current_request['random'] == evaluated_request['random']:
            if priority is None:
                priority = idx+1
            else:
                raise Exception("Two jobs try to access in write mode at the same ressource.")
    return priority

def get_requests( request_dir, shared_file ):
    """
    @summary: Returns the list of access requests on shared file.
    @param request_dir: [str] The path to the directory where the temporary
                        files (request and lock) are stored.
    @param shared_file: [str] The path to the file shared in writing mode
                              between the concurrent processes.
    @return: [list] The list of access requests.
    """
    all_requests = list()
    pattern = os.path.basename(shared_file) + "_accessRequest_[^\-]+\-\d+\-\d+"
    for request_file in os.listdir(request_dir):
        if re.match(pattern, request_file):
            try:
                fh_request = open(os.path.join(request_dir, request_file))
                all_requests.append( json.load(fh_request) )
                fh_request.close()
            except:
                pass
    return all_requests

def stopRetry( priorities, max_stable_priorities ):
    """
    @summmary: Checks the evolution of the priority along the access retries and
               returns true if the priority does not change during last N
               retries. This is to prevent deadlock.
    @param priorities: [list] The priorities of each access retries.
    @param max_stable_priorities: [int] The maximum number of retry with the
                                  same priority.
    @return: [bool] Returns true if the priority does not change.
    """
    if len(priorities) < max_stable_priorities:
        return False
    stop_retry = True
    for idx in range(max_stable_priorities-1):
        # With max_stable_priorites = 4:
        #     idx = 0: priorities[-1] != priorities[-2]
        #     idx = 1: priorities[-2] != priorities[-3]
        #     idx = 2: priorities[-3] != priorities[-4]
        if priorities[-(1+idx)] != priorities[-(2+idx)]:
            stop_retry = False
    return stop_retry

def exec_on_shared( process_fct, shared_file, tmp_dir="/tmp", time_between_retry=0.7, max_stable_priorities=100, metadata=None ):
    """
    @summmary: Manages concurrent access in writing mode between several
               processes on a shared file.
    @param process_fct: [func] The function executed when the shared ressource
                        is available for the current job.
    @param shared_file: [str] The path to the file shared in writing mode
                        between the concurrent processes.
    @param tmp_dir: [str] The path to the directory where the temporary files
                    (request and lock) are stored.
    @param time_between_retry: [float] the number of seconds between each
                               retry.
    @param max_stable_priorities: [int] The number of retry with the same
                                  priority for consider situation as a
                                  deadlock.
    @param metadata: [dict] The metadata added in access request file.
    @return: The process_fct return or None if the process_fct does not have
             return.
    @note: Bug if 1 node with a late timestamp executes the reservation, the
           sleep and the priority check between the priority check and the lock
           creation of an other node with a valid timestamp.
    """
    fct_return = None
    retry = True
    lock_file = os.path.join( tmp_dir, os.path.basename(shared_file) + "_lock" )

    # Get request info
    current_request = {
        'timestamp': time.time(),
        'PID': os.getpid(),
        'random': random.randint(1, 10000000000000000),
        'metadata': metadata
    }

    # Set request file
    request_filename = "{}_accessRequest_{}-{}-{}".format(os.path.basename(shared_file), current_request['timestamp'], current_request['PID'], current_request['random'])
    current_request_file = os.path.join( tmp_dir, request_filename )

    try:
        # Write request file
        fh_request = open(current_request_file, "w")
        fh_request.write( json.dumps(current_request) )
        fh_request.close()

        # Wait
        time.sleep( time_between_retry )

        # Try to access at the shared ressource
        priorities = list()
        while retry:
            access_requests = get_requests( tmp_dir, shared_file ) # Retrieve all access requests
            priorities.append( get_priority(access_requests, current_request) ) # Return the position of the current request in requests execution order
            if priorities[-1] == 1 and not os.path.exists(lock_file): # lock_file prevents error with jobs launched after the job with access to the ressource but on node with a bad timestamp
                open(lock_file, "w").close()
                os.remove( current_request_file )
                # Process
                fct_return = process_fct()
                retry = False
            else:
                if stopRetry(priorities, max_stable_priorities):
                    raise Exception("Dead lock to access at the ressource.")
                time.sleep( time_between_retry )
    finally:
        # Delete current access request
        if os.path.exists(current_request_file):
            os.remove( current_request_file )
        if os.path.exists(lock_file):
            os.remove( lock_file )

    return fct_return