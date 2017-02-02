# Copyright (c) 2011- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

""" cctools Makeflow log module """



from cctools.compat import map
from cctools.error  import raise_parser_error, ParserError
from cctools.util   import catch_exception, dump, iterable

import collections
import csv
import json
import operator
import sys
import time


__all__ = ['LogParserError', 'LogParserMixin', 'LogDataMixin', 'Log',
           'Node', 'NodeList', 'Event',
           'Reporter', 'RawReporter', 'CSVReporter']


# Makeflow Log

class LogParserError(ParserError):
    """ This is the Makeflow log parser error. """
    pass


class LogParserMixin(object):
    """ This is the Makeflow log parser mixin. """

    _PARSERS = {
        '# NODE'        : lambda s, l: s._parse_node(l),
        '# PARENTS'     : lambda s, l: s._parse_parents(l),
        '# SYMBOL'      : lambda s, l: s._parse_symbol(l),
        '# SOURCES'     : lambda s, l: s._parse_sources(l),
        '# TARGETS'     : lambda s, l: s._parse_targets(l),
        '# COMMAND'     : lambda s, l: s._parse_command(l),
        '# STARTED'     : lambda s, l: s._parse_started(l),
        '# FAILED'      : lambda s, l: s._parse_failed(l),
        '# ABORTED'     : lambda s, l: s._parse_aborted(l),
        '# COMPLETED'   : lambda s, l: s._parse_completed(l),
    }

    def parse(self):
        """ Parse the log stream.

        If a parsing error occurs, a :class:`LogParserError` is thrown.
        """
        stream = open(self.path, 'r')
        for line in stream:
            line = line.strip()
            key = line.split('\t')[0]
            try:
                LogParserMixin._PARSERS[key](self, line)
            except KeyError:
                if not line.startswith('#'):
                    self._parse_event(line)
        stream.close()

    @raise_parser_error(ValueError, 'node', LogParserError)
    def _parse_node(self, line):
        """ Parse a node and add to :class:`Log`. """
        tokens = line.split('\t')
        node_id = int(tokens[1])
        node_command = tokens[2]
        self.add_node(Node(node_id, node_command))

    @raise_parser_error(ValueError, 'parents', LogParserError)
    def _parse_parents(self, line):
        """ Parse parents and add :class:`Node` to :class:`Log`. """
        tokens = line.split('\t')
        node_id = int(tokens[1])
        node_parents = [int(i) for i in tokens[2:]]
        self.nodes[node_id].parents = node_parents

    @raise_parser_error(ValueError, 'sources', LogParserError)
    def _parse_sources(self, line):
        """ Parse sources and add :class:`Node` to :class:`Log`. """
        tokens = line.split('\t')
        node_id = int(tokens[1])
        node_sources = tokens[2:]
        self.nodes[node_id].sources = node_sources

    @raise_parser_error(ValueError, 'symbol', LogParserError)
    def _parse_symbol(self, line):
        """ Parse symbol and add :class:`Node` to :class:`Log`. """
        tokens = line.split('\t')
        node_id = int(tokens[1])
        node_symbol = tokens[2]
        self.nodes[node_id].symbol = node_symbol

    @raise_parser_error(ValueError, 'targets', LogParserError)
    def _parse_targets(self, line):
        """ Parse targets and add :class:`Node` to :class:`Log`. """
        tokens = line.split('\t')
        node_id = int(tokens[1])
        node_targets = tokens[2:]
        self.nodes[node_id].targets = node_targets

    @raise_parser_error(ValueError, 'command', LogParserError)
    def _parse_command(self, line):
        """ Parse command and add :class:`Node` to :class:`Log`. """
        tokens = line.split('\t')
        node_id = int(tokens[1])
        node_command = tokens[2]
        self.nodes[node_id].command = node_command

    @raise_parser_error((ValueError, IndexError), 'started', LogParserError)
    def _parse_started(self, line):
        """ Parse start time and adjust :class:`Log`. """
        self.starts.append(float(line.split('\t')[1])/1000000.0)
        self.state = 'started'

    @raise_parser_error((ValueError, IndexError), 'failed', LogParserError)
    def _parse_failed(self, line):
        """ Parse failure time and adjust :class:`Log`. """
        self.failures.append(float(line.split('\t')[1])/1000000.0)
        self.state = 'failed'

    @raise_parser_error((ValueError, IndexError), 'aborted', LogParserError)
    def _parse_aborted(self, line):
        """ Parse abortion time and adjust :class:`Log`. """
        self.abortions.append(float(line.split('\t')[1])/1000000.0)
        self.state = 'aborted'

    @raise_parser_error((ValueError, IndexError), 'completed', LogParserError)
    def _parse_completed(self, line):
        """ Parse completion time and adjust :class:`Log`. """
        self.completions.append(float(line.split('\t')[1])/1000000.0)
        self.state = 'completed'

    @raise_parser_error((ValueError, LogParserError), 'event', LogParserError)
    def _parse_event(self, line):
        """ Parse an event and add to :class:`Log`. """
        self.add_event(Event(*[int(i) for i in line.split()]))


class LogDataMixin(object):
    """ This is the Makeflow log data mixin.

    A :class:`LogDataMixin` object contains the following fields:

    - `path`                     -- Path of the Makeflow log file.
    - `starts`	                 -- List of start timestamps.
    - `failures`	         -- List of failure timestamps.
    - `abortions`	         -- List of failure timestamps.
    - `completions`	         -- List of completion timestamps.
    - `elapsed_time`	         -- Elapsed time of the Makeflow execution.
    - `percent_completed`	 -- Percentage of Makeflow tasks completed.
    - `average_tasks_per_second` -- Average number of tasks completed / second.
    - `current_tasks_per_second` -- Current number of tasks completed / second.
    - `estimated_time_left`	 -- Estimated time left to complete Makeflow.
    - `state`	                 -- State of the Makeflow.
    - `finished`	         -- Whether or not the Makeflow is finished executing.
    - `goodput`	                 -- Amount of good compute time.
    - `badput`	                 -- Amount of bad compute time.

    A :class:`LogDataMixin` object also contains the following information:

    - `events`                   -- List of Makeflow log :class:`Event`\s.
    - `nodes`                    -- List of Makeflow log :class:`Node`\s.
    """

    #: List of available log information provided after parsing.
    FIELDS = [
        'path',
        'starts',
        'failures',
        'abortions',
        'completions',
        'elapsed_time',
        'percent_completed',
        'average_tasks_per_second',
        'current_tasks_per_second',
        'estimated_time_left',
        'state',
        'finished',
        'goodput',
        'badput',
    ]

    #: Maximum number of events to store.
    MAX_EVENTS = 1000

    def __init__(self):
        self.state = None
        self.starts = []
        self.failures = []
        self.abortions = []
        self.completions = []
        self.events = collections.deque(maxlen=LogDataMixin.MAX_EVENTS)
        self.nodes = NodeList()

    @property
    def dag(self):
        """ Return nodes organized as a DAG.

        TODO: implement dag creation
        """
        return self.nodes

    @property
    @catch_exception((TypeError, IndexError), 0)
    def elapsed_time(self):
        """ Return elapsed time of Makeflow execution.

        If :meth:`finished`, then return elapsed time based on last completion
        time and last start time.  Otherwise, return elapsed time based on
        current time and last start time.
        """
        if self.finished:
            for tlist in [self.completions, self.failures, self.abortions]:
                try:
                    return tlist[-1] - self.starts[-1]
                except IndexError:
                    continue
            return None
        else:
            return time.time() - self.starts[-1]

    @property
    @catch_exception(ZeroDivisionError, 0)
    def percent_completed(self):
        """ Return percent of nodes that have reached completed state. """
        return float(self.nodes.completed) / self.nodes.total * 100.0

    @property
    @catch_exception(ZeroDivisionError, 0)
    def average_tasks_per_second(self):
        """ Return average number of tasks completed per second. """
        return float(self.nodes.completed) / self.elapsed_time

    @property
    def current_tasks_per_second(self):
        """ Return current rate of tasks completed per second.

        If makeflow is finished, then ``0`` is returned, otherwise, use all the
        events within the last ``60`` seconds to compute the current rate.
        """
        if self.finished:
            return 0

        current_time = time.time()
        start_event = None

        for event in reversed(self.events):
            start_event = event
            if current_time - start_event.timestamp > 60.0:
                break

        if start_event:
            last_event = self.events[-1]
            n = last_event.nodes_completed - start_event.nodes_completed
            try:
                return float(n) / min(60.0, last_event.timestamp - start_event.timestamp)
            except ZeroDivisionError:
                pass
        return 0

    @property
    @catch_exception(ZeroDivisionError, None)
    def estimated_time_left(self):
        """ Return estimated time left based on current completion rate. """
        return (self.nodes.total - self.nodes.completed) / \
                self.current_tasks_per_second

    @property
    def finished(self):
        return self.state in ['failed', 'aborted', 'completed']

    @property
    def goodput(self):
        """ Return aggregate amount of good computation time. """
        return sum([n.goodput for n in self.nodes])

    @property
    def badput(self):
        """ Return aggregate amount of bad computation time. """
        return sum([n.badput for n in self.nodes])


class Log(LogDataMixin, LogParserMixin):
    """ This is the Makeflow log class.

    A :class:`Log` object is a composite of both :class:`LogDataMixin` and
    :class:`LogParserMixin`.
    """

    def __init__(self, path):
        LogDataMixin.__init__(self)
        LogParserMixin.__init__(self)

        self.path = path
        self.offset = 0

    def add_event(self, event):
        """ Add :class:`Event` to :class:`Log`. """
        # Update individual node information
        self.nodes[event.node_id].update(event)

        # Update total node information
        self.nodes.waiting = event.nodes_waiting
        self.nodes.running = event.nodes_running
        self.nodes.completed = event.nodes_completed
        self.nodes.failed = event.nodes_failed
        self.nodes.aborted = event.nodes_aborted

        # Add event to instance list
        self.events.append(event)

    def add_node(self, node):
        """ Add :class:`Node` to :class:`Log`. """
        if node.id >= len(self.nodes):
            self.nodes.extend([None]*(node.id - len(self.nodes) + 1))

        self.nodes[node.id] = node


class Node(object):
    """ This is the Makeflow log node class.

    A :class:`Node` object contains the following fields:

    - `id`                  -- ID of :class:`Node`.
    - `command`             -- Command executed by :class:`Node`.
    - `original_command`    -- Original command of :class:`Node`.
    - `parents`             -- Parent nodes of :class:`Node`.
    - `sources`             -- Input source files of :class:`Node`.
    - `targets`             -- Output target files of :class:`Node`.
    - `states`              -- Sequence of states reached during execution.
    - `state`               -- Last state of :class:`Node`.
    - `timestamps`          -- List of :class:`Node`\'s timestamps.
    - `job_ids`             -- List of batch job ids associated with :class:`Node`.
    - `attempts`            -- Number of times execution was attempted.
    - `failures`            -- Number of times execution failed.
    - `abortions`           -- Number of times execution was aborted.
    - `goodputs`            -- List of good computation execution times.
    - `goodput`             -- Total amount of good computation.
    - `badputs`             -- List of bad computation execution times.
    - `badput`              -- Total amount of bad computation.
    """

    #: List of available node information provided after parsing.
    FIELDS = [
        'id',
        'command',
        'original_command',
        'parents',
        'sources',
        'targets',
        'states',
        'state',
        'timestamps',
        'elapsed_time',
        'job_ids',
        'attempts',
        'failures',
        'abortions',
        'goodputs',
        'goodput',
        'badputs',
        'badput',
    ]

    #: Constant for *WAITING* :class:`Node` state.
    WAITING = 0
    #: Constant for *RUNNING* :class:`Node` state.
    RUNNING = 1
    #: Constant for *COMPLETED* :class:`Node` state.
    COMPLETED = 2
    #: Constant for *FAILED* :class:`Node` state.
    FAILED = 3
    #: Constant for *ABORTED* :class:`Node` state.
    ABORTED = 4

    def __init__(self, id, command):
        self.id = id
        self.command = command
        self.original_command = command
        self.parents = []
        self.sources = []
        self.targets = []
        self.goodputs = []
        self.badputs = []
        self.timestamps = []
        self.states = []
        self.symbol = None
        self.job_ids = set()

    def update(self, event):
        """ Update :class:`Node` with information from :class:`Event`. """
        try:
            if self.states[-1] == Node.RUNNING:
                timediff = event.timestamp - self.timestamps[-1]
                if event.node_state == Node.COMPLETED:
                    self.goodputs.append(timediff)
                else:
                    self.badputs.append(timediff)
        except IndexError:
            pass

        self.timestamps.append(event.timestamp)
        self.states.append(event.node_state)
        self.job_ids.add(event.node_job_id)

    @property
    @catch_exception(IndexError, None)
    def state(self):
        return self.states[-1]

    @property
    def elapsed_time(self):
        try:
            return self.timestamps[-1] - self.timestamps[0]
        except IndexError:
            return 0


    @property
    def attempts(self):
        return len([s for s in self.states if s == Node.RUNNING])

    @property
    def failures(self):
        return len([s for s in self.states if s == Node.FAILED])

    @property
    def abortions(self):
        return len([s for s in self.states if s == Node.ABORTED])

    @property
    def goodput(self):
        return sum(self.goodputs)

    @property
    def badput(self):
        return sum(self.badputs)

class NodeList(list):
    """ This is the Makeflow log node list class.

    A :class:`NodeList` object contains the following fields:

    - `waiting`   -- Number of :class:`Node`\s in :data:`~Node.WAITING` state.
    - `running`   -- Number of :class:`Node`\s in :data:`~Node.RUNNING` state.
    - `completed` -- Number of :class:`Node`\s in :data:`~Node.COMPLETED` state.
    - `failed`    -- Number of :class:`Node`\s in :data:`~Node.FAILED` state.
    - `aborted`   -- Number of :class:`Node`\s in :data:`~Node.ABORTED` state.
    - `retried`   -- Number of :class:`Node`\s in that have been retried.
    - `total`     -- Total number of :class:`Node`\s.
    """

    #: List of available node list information provided after parsing.
    FIELDS = [
        'waiting',
        'running',
        'completed',
        'failed',
        'aborted',
        'retried',
        'total',
    ]

    def __init__(self):
        list.__init__(self)
        self.waiting = 0
        self.running = 0
        self.completed = 0
        self.failed = 0
        self.aborted = 0

    @property
    def retried(self):
        """ Return aggregate number or retries. """
        return sum([n.attempts > 1 for n in self])

    @property
    def total(self):
        """ Return total number of nodes. """
        return len(self)


class Event(object):
    """ This is the Makeflow log event class.

    An :class:`Event` object contains the following fields:

    - `timestamp`       -- Timestamp of the event.
    - `node_id`         -- ID of the :class:`Node` the event is about.
    - `node_state`      -- New state of :class:`Node`.
    - `node_job_id`     -- Batch job ID of :class:`Node`.
    - `nodes_waiting`   -- Number of nodes in *WAITING* state.
    - `nodes_running`   -- Number of nodes in *RUNNING* state.
    - `nodes_completed` -- Number of nodes have *COMPLETED*.
    - `nodes_failed`    -- Number of nodes have *FAILED*.
    - `nodes_aborted`   -- Number of nodes have been *ABORTED*.
    - `nodes_total`     -- Total number of nodes in Makeflow.
    """

    #: List of available event information provided after parsing.
    FIELDS = [
        'timestamp',
        'node_id',
        'node_state',
        'node_job_id',
        'nodes_waiting',
        'nodes_running',
        'nodes_completed',
        'nodes_failed',
        'nodes_aborted',
        'nodes_total',
    ]

    def __init__(self, *args):
        if len(Event.FIELDS) != len(args):
            raise LogParserError(Event, 'missing fields')

        for field, value in zip(Event.FIELDS, args):
            self.__dict__[field] = value

        # Timestamps are in microseconds, so convert to seconds
        self.timestamp = float(self.timestamp)/1000000.0


# Makflow Log Reporters

class Reporter(object):
    """ This is the base Makeflow reporter class. """

    REPORTERS = {
        'raw' : lambda: RawReporter(),
        'csv' : lambda: CSVReporter(),
        'json': lambda: JSONReporter(),
    }

    @staticmethod
    def select(format):
        """ Return reporter functions for specified `format`. """
        return Reporter.REPORTERS[format]()

    def report(self, log, stream=None, verbose=False, sort_field=None, filters=None):
        """ Report to `stream`. """
        self.report_log(log, stream)
        if verbose:
            if sort_field:
                log.nodes.sort(key=operator.attrgetter(sort_field))
            if filters:
                nodes = [node for node in log.nodes if all([eval(f, {'node': node}) for f in filters])]
            else:
                nodes = log.nodes

            for node in nodes:
                self.report_node(node)

    def report_log(self, log, stream=None):
        """ Report :class:`Log` object. """
        raise NotImplementedError

    def report_node(self, node, stream=None):
        """ Report :class:`Node` object. """
        raise NotImplementedError


class RawReporter(Reporter):
    """ This Makeflow reporter outputs a raw text dump. """

    def report_log(self, log, stream=None):
        """ Use :func:`~cctools.util.dump` to write :class:`Log` to `stream`. """
        stream = stream or sys.stdout

        for log_field in Log.FIELDS:
            dump('log.' + log_field, stream=stream)

        for node_list_field in NodeList.FIELDS:
            dump('log.nodes.' + node_list_field, stream=stream)

    def report_node(self, node, stream=None):
        """ Use :func:`~cctools.util.dump` to write :class:`Node` to `stream`. """
        stream = stream or sys.stdout

        print(file=stream)
        for node_field in Node.FIELDS:
            dump('node.' + node_field, stream=stream)


class CSVReporter(Reporter):
    """ This Makeflow reporter outputs CSV. """

    def report_log(self, log, stream=None):
        """ Write :class:`Log` in CSV format to `stream`. """
        stream = stream or sys.stdout

        log_fields = [getattr(log, f) for f in Log.FIELDS]
        log_strings = [' '.join(map(str, f))
            if iterable(f) and not isinstance(f, str) else str(f)
            for f in log_fields]

        node_list_fields = [getattr(log.nodes, f) for f in NodeList.FIELDS]
        node_list_strings = [' '.join(map(str, f))
            if iterable(f) and not isinstance(f, str) else str(f)
            for f in node_list_fields]

        csv_writer = csv.writer(stream)
        csv_writer.writerow(log_strings + node_list_strings)

    def report_node(self, node, stream=None):
        """ Write :class:`Node` in CSV format to `stream`. """
        stream = stream or sys.stdout

        node_fields = [getattr(node, f) for f in Node.FIELDS]
        node_strings = [' '.join(map(str, f))
            if iterable(f) and not isinstance(f, str) else str(f)
            for f in node_fields]

        csv_writer = csv.writer(stream)
        csv_writer.writerow(node_strings)


class JSONReporter(Reporter):
    """ This Makeflow reporter outputs JSON. """

    def report(self, log, stream=None, verbose=False, sort_field=None, filters=None):
        """ Report in JSON format to `stream`. """
        stream = stream or sys.stdout

        json_dict = {'log': {}}
        for f in Log.FIELDS:
            json_dict['log'][f] = JSONReporter._get_field_value(log, f)

        json_dict['log']['nodes'] = {}
        for f in NodeList.FIELDS:
            json_dict['log']['nodes'][f] = JSONReporter._get_field_value(log.nodes, f)

        if verbose:
            if sort_field:
                log.nodes.sort(key=operator.attrgetter(sort_field))
            if filters:
                nodes = [node for node in log.nodes if all([eval(f, {'node': node}) for f in filters])]
            else:
                nodes = log.nodes

            json_dict['node'] = {}
            for node in nodes:
                node_dict = {}
                for f in Node.FIELDS:
                    node_dict[f] = JSONReporter._get_field_value(node, f)

                json_dict['node'][node.id] = node_dict

            json_dict['log']['events'] = []
            for event in log.events:
                event_dict = {}
                for f in Event.FIELDS:
                    event_dict[f] = JSONReporter._get_field_value(event, f)

                json_dict['log']['events'].append(event_dict)


        json.dump(json_dict, stream, indent=2)
        stream.write('\n')

    @staticmethod
    def _get_field_value(object, field):
        value = getattr(object, field)
        if iterable(value) and not isinstance(value, str):
            return list(value)
        else:
            return value

# vim: sts=4 sw=4 ts=8 expandtab ft=python
