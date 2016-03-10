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

import re
import sys
import smtplib
import socket
import math
import shutil

try:
    import DNS
    ServerError = DNS.ServerError
except:
    DNS = None
    class ServerError(Exception): pass

def robust_rmtree(path, logger=None, max_retries=6):
    """Robustly tries to delete paths.
    Retries several times (with increasing delays) if an OSError
    occurs.  If the final attempt fails, the Exception is propagated
    to the caller.
    """
    dt = 1
    for i in range(max_retries):
        try:
            shutil.rmtree(path)
            return
        except OSError:
            if logger:
                logger.info('Unable to remove path: %s' % path)
                logger.info('Retrying after %d seconds' % dt)
            time.sleep(dt)
            dt *= 2

    # Final attempt, pass any Exceptions up to caller.
    shutil.rmtree(path)

def display_error_message(msg):
    sys.stderr.write("\033[91mError: "+msg+"\n\033[0m")
    sys.exit(1)

def display_info_message(msg, with_exit=False):
    sys.stderr.write("\033[93mInfo: "+msg+"\n\033[0m")
    if with_exit: sys.exit(1)

def which(program):
    """
    Return if the asked program exist in the user path
      @param options : the options asked by the user
    """
    import os
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

def get_file_base (file):
    """
    Return the file base
      @param file: input file
    """
    # First import required libraries
    import os
    
    file_base = os.path.splitext(os.path.basename(file))[0]
    if os.path.splitext(file)[1] == ".gz":
        file_base = os.path.splitext(file_base)[0]
    return file_base

def get_nb_string(value, length=6):  
    """
    Return a string of n caracters.
      @param value: the value to get representation
      @param length: the final length required
    """
    zeros = ""
    s_value = str(value)
    for i in range(length - len(s_value)):
        zeros += "0";
    s_value = zeros + s_value
    return s_value

def get_nb_octet(size):
    """
    Return the number of bytes: value has to be formated like this: 5Mb, 20Gb ...
    """
    octets_link = ["bytes", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb", "Zb"]
    if size.endswith("bytes"):
        unit = "bytes"
        isize = size[:len(size)-5]
    else:
        unit = size[len(size)-2:len(size)]
        isize = size[:len(size)-2]
    pow_val = int(octets_link.index(unit)) * 10
    val = pow(2, pow_val)
    nb_octet = float(isize) * val
    return nb_octet

def get_octet_string_representation(size):
    """
    Return the string representation of a byte
    """
    octets_link = ["bytes", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb", "Zb"]
    p = int(math.ceil(float(len(str(size)))/float(3) - float(1)))
    pow_needed = p * 10
    pow_needed = pow(2, pow_needed)
    value = str(float(size)/float(pow_needed))
    tmp = value.split(".")
    value = tmp[0] + "." + tmp[1][:2]
    try:
        value = value + " " + octets_link[p]
    except:
        raise TypeError("In core.common:project_id unexpected input value for size: " + str(size))
    return str(value)

def get_argument_pattern( list, start_number=1 ):
    """
    Return the argument pattern for arguments files. Ex : with 3 element in list this function returns ["${1} ${2} ${3}", 4].
      @param list : the list of files.
      @param start_number : number of the first argument.
    """
    arg_pattern = ""
    next_number = start_number
    for elt in list:
        arg_pattern += ' ${' + str(next_number) + '}'
        next_number += 1
        
    return [arg_pattern, next_number]

# All we are really doing is comparing the input string to one
# gigantic regular expression.  But building that regexp, and
# ensuring its correctness, is made much easier by assembling it
# from the "tokens" defined by the RFC.  Each of these tokens is
# tested in the accompanying unit test file.
#
# The section of RFC 2822 from which each pattern component is
# derived is given in an accompanying comment.
#
# (To make things simple, every string below is given as 'raw',
# even when it's not strictly necessary.  This way we don't forget
# when it is necessary.)
#
WSP = r'[ \t]'                                       # see 2.2.2. Structured Header Field Bodies
CRLF = r'(?:\r\n)'                                   # see 2.2.3. Long Header Fields
NO_WS_CTL = r'\x01-\x08\x0b\x0c\x0f-\x1f\x7f'        # see 3.2.1. Primitive Tokens
QUOTED_PAIR = r'(?:\\.)'                             # see 3.2.2. Quoted characters
FWS = r'(?:(?:' + WSP + r'*' + CRLF + r')?' + \
            WSP + r'+)'                                    # see 3.2.3. Folding white space and comments
CTEXT = r'[' + NO_WS_CTL + \
                r'\x21-\x27\x2a-\x5b\x5d-\x7e]'              # see 3.2.3
CCONTENT = r'(?:' + CTEXT + r'|' + \
                     QUOTED_PAIR + r')'                        # see 3.2.3 (NB: The RFC includes COMMENT here
                                                                                                         # as well, but that would be circular.)
COMMENT = r'\((?:' + FWS + r'?' + CCONTENT + \
                    r')*' + FWS + r'?\)'                       # see 3.2.3
CFWS = r'(?:' + FWS + r'?' + COMMENT + ')*(?:' + \
             FWS + '?' + COMMENT + '|' + FWS + ')'         # see 3.2.3
ATEXT = r'[\w!#$%&\'\*\+\-/=\?\^`\{\|\}~]'           # see 3.2.4. Atom
ATOM = CFWS + r'?' + ATEXT + r'+' + CFWS + r'?'      # see 3.2.4
DOT_ATOM_TEXT = ATEXT + r'+(?:\.' + ATEXT + r'+)*'   # see 3.2.4
DOT_ATOM = CFWS + r'?' + DOT_ATOM_TEXT + CFWS + r'?' # see 3.2.4
QTEXT = r'[' + NO_WS_CTL + \
                r'\x21\x23-\x5b\x5d-\x7e]'                   # see 3.2.5. Quoted strings
QCONTENT = r'(?:' + QTEXT + r'|' + \
                     QUOTED_PAIR + r')'                        # see 3.2.5
QUOTED_STRING = CFWS + r'?' + r'"(?:' + FWS + \
                                r'?' + QCONTENT + r')*' + FWS + \
                                r'?' + r'"' + CFWS + r'?'
LOCAL_PART = r'(?:' + DOT_ATOM + r'|' + \
                         QUOTED_STRING + r')'                    # see 3.4.1. Addr-spec specification
DTEXT = r'[' + NO_WS_CTL + r'\x21-\x5a\x5e-\x7e]'    # see 3.4.1
DCONTENT = r'(?:' + DTEXT + r'|' + \
                     QUOTED_PAIR + r')'                        # see 3.4.1
DOMAIN_LITERAL = CFWS + r'?' + r'\[' + \
                                 r'(?:' + FWS + r'?' + DCONTENT + \
                                 r')*' + FWS + r'?\]' + CFWS + r'?'  # see 3.4.1
DOMAIN = r'(?:' + DOT_ATOM + r'|' + \
                 DOMAIN_LITERAL + r')'                       # see 3.4.1
ADDR_SPEC = LOCAL_PART + r'@' + DOMAIN               # see 3.4.1

# A valid address will match exactly the 3.4.1 addr-spec.
VALID_ADDRESS_REGEXP = '^' + ADDR_SPEC + '$'

def validate_email(email, check_mx=False,verify=False):

    """Indicate whether the given string is a valid email address
    according to the 'addr-spec' portion of RFC 2822 (see section
    3.4.1).  Parts of the spec that are marked obsolete are *not*
    included in this test, and certain arcane constructions that
    depend on circular definitions in the spec may not pass, but in
    general this should correctly identify any email address likely
    to be in use as of 2011."""
    try:
        assert re.match(VALID_ADDRESS_REGEXP, email) is not None
        check_mx |= verify
        if check_mx:
            if not DNS: raise Exception('For check the mx records or check if the email exists you must have installed pyDNS python package')
            DNS.DiscoverNameServers()
            hostname = email[email.find('@')+1:]
            mx_hosts = DNS.mxlookup(hostname)
            for mx in mx_hosts:
                try:
                    smtp = smtplib.SMTP()
                    smtp.connect(mx[1])
                    if not verify: return True
                    status, _ = smtp.helo()
                    if status != 250: continue
                    smtp.mail('')
                    status, _ = smtp.rcpt(email)
                    if status != 250: return False
                    break
                except smtplib.SMTPServerDisconnected: #Server not permits verify user
                    break
                except smtplib.SMTPConnectError:
                    continue
    except (AssertionError, ServerError): 
        return False
    return True