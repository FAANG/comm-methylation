# Copyright (c) 2012- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

""" cctools Makeflow dag module """



from cctools.compat import map
from cctools.error  import raise_parser_error, ParserError
from cctools.util   import catch_exception, dump, iterable, split_pair

import itertools
import os
import shlex
import sys


class DAGParserError(ParserError):
    pass


class DAG(object):
    def __init__(self, path=None, work_dir=None):
        self.path      = os.path.abspath(path)
        self.work_dir  = os.path.abspath(work_dir or os.path.abspath(os.path.dirname(path)))
        self.nodes     = []
        self.exports   = set()
        self.variables = []
        self.counter   = itertools.count()
        self.children  = []

    def parse(self, path=None):
        self.path = path or self.path
        if not self.path:
            raise DAGParserError(self, 'no DAG file specified')

        try:
            self.dag_file = open(self.path, 'r')
        except IOError as e:
            raise DAGParserError(self, e)

        while True:
            line = self.parse_readline()
            if line is None or line.startswith('#'):
                break

            if   '=' in line:
                self.parse_variable(line)
            elif ':' in line:
                self.parse_node(line)
            elif line.startswith('export'):
                self.parse_export(line)

        self.dag_file.close()

    def parse_readline(self):
        while True:
            line = self.dag_file.readline()
            if len(line) == 0:
                return None

            line = line.strip()
            if len(line) == 0:
                continue
            return line

    def parse_variable(self, line, local=False, variable_list=None):
        if '+=' in line:
            name, value = split_pair(line, '+=')
            append      = True
        else:
            name, value = split_pair(line, '=')
            append      = False

        if variable_list is None:
            variable_list = self.variables

        variable_list.append(DAGVariable(name, value, local, append))

    def parse_export(self, line):
        self.exports.update(line.split()[1:])

    def parse_node(self, line):
        output_files, input_files = [set(shlex.split(s)) for s in line.split(':')]
        command   = None
        symbol    = None
        variables = []
        while True:
            line = self.parse_readline()
            if   line.startswith('@'):
                self.parse_variable(line[1:], local=True, variable_list=variables)
            elif line.startswith('# SYMBOL'):
                symbol = line.split('\t')[1]
            elif line.startswith('#'):
                continue
            else:
                command = line
                break

        self.nodes.append(
            DAGNode(next(self.counter), output_files, input_files, variables, command, symbol))

        # Reset symbol after we parse Node
        self.symbol = None

        # Detect nested Makeflows
        if 'MAKEFLOW' in command:
            command_list = shlex.split(command)
            self.children.append(DAG(command_list[1], command_list[2]))

    def dump(self, file=sys.stdout):
        for node in self.nodes:
            file.write(str(node) + '\n')

        for variable in self.variables:
            file.write(str(variable) + '\n')

        for export in self.exports:
            file.write('export {0}\n'.format(export))


class DAGNode(object):
    def __init__(self, id, output_files, input_files, variables, command, symbol=None):
        self.id           = id
        self.output_files = output_files
        self.input_files  = input_files
        self.command      = command
        self.variables    = variables
        self.symbol       = symbol

    def __str__(self):
        if self.symbol:
            symbol = '\t# SYMBOL\t' + self.symbol + '\n'
        else:
            symbol = ''
        return '{0}: {1}\n{2}{3}\t{4}'.format(
            ' '.join(self.output_files),
            ' '.join(self.input_files),
            symbol,
            '\t' + '\n\t'.join(map(str, self.variables)) + '\n' if self.variables else '',
            self.command)


class DAGVariable(object):
    def __init__(self, name, value, local=False, append=False):
        self.name   = name
        self.value  = value
        self.local  = local
        self.append = append

    def __str__(self):
        return '{0}{1}{2}={3}'.format(
            '@' if self.local else '',
            self.name,
            '+' if self.append else '',
            self.value)

# vim: set sts=4 sw=4 ts=8 expandtab ft=python:
