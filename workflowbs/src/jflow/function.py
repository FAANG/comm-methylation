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

from weaver.compat  import execfile
from weaver.logger  import D_SCRIPT, debug, fatal
from weaver.nest    import Nest
from weaver.options import Options
from weaver.util    import Container
from weaver.script  import Script
from weaver.script  import ABSTRACTIONS
from weaver.script  import DATASETS
from weaver.script  import FUNCTIONS
from weaver.script  import NESTS
from weaver.script  import OPTIONS
from weaver.script  import STACKS

import weaver.logger

import collections
import os
import sys
import time

class Wfunction(object):
    """ Weaver Script class.

    Parses command line environment and sets up run-time configuration.
    """

    def __init__(self, function=None, force=False, import_builtins=True, output_directory=None,
                 execute_dag=False, engine_wrapper=None, engine_arguments=None, args=[]):
        self.function = function
        self.arguments = args
        self.force = force # Ignore warnings
        self.import_builtins = True # Load built-ins
        if output_directory is None:
            self.output_directory = os.curdir # Where to create artifacts
        else:
            self.output_directory = output_directory
        self.start_time = time.time() # Record beginning of compiling
        self.options = Options()
        self.nested_abstractions = False
        self.inline_tasks = 1
        self.execute_dag         = execute_dag
        self.globals             = {}
        self.engine_wrapper      = engine_wrapper
        self.engine_arguments    = engine_arguments
        self.include_symbols     = False

        debug(D_SCRIPT, 'force               = {0}'.format(self.force))
        debug(D_SCRIPT, 'import_builtins     = {0}'.format(self.import_builtins))
        debug(D_SCRIPT, 'output_directory    = {0}'.format(self.output_directory))
        debug(D_SCRIPT, 'start_time          = {0}'.format(self.start_time))
        debug(D_SCRIPT, 'options             = {0}'.format(self.options))
        debug(D_SCRIPT, 'nested_abstractions = {0}'.format(self.nested_abstractions))
        debug(D_SCRIPT, 'inline_tasks        = {0}'.format(self.inline_tasks))
        debug(D_SCRIPT, 'execute_dag         = {0}'.format(self.execute_dag))
        debug(D_SCRIPT, 'engine_wrapper      = {0}'.format(self.engine_wrapper))
        debug(D_SCRIPT, 'engine_arguments    = {0}'.format(self.engine_arguments))

    def _import(self, module, symbols):
        """ Import ``symbols`` from ``module`` into global namespace. """
        # Import module
        m = 'weaver.{0}'.format(module)
        m = __import__(m, self.globals, self.globals, symbols, -1)

        # Import symbols from module into global namespace, which we store as
        # an attribute for later use (i.e. during compile)
        for symbol in symbols:
            self.globals[symbol] = getattr(m, symbol)
            debug(D_SCRIPT, 'Imported {0} from {1}'.format(symbol, module))

    def compile(self):
        """ Compile script in the specified working directory. """
        # Save active script instance and set this one as active
        work_dir = self.output_directory

        # Add nest path and path to script to Python module path to allow
        # for importing modules outside of $PYTHONPATH
        sys.path.insert(0, os.path.abspath(os.path.dirname(work_dir)))

        # Load built-ins if specified on command line.  If built-ins are
        # not automatically loaded by the Script object, then the user must
        # load them manually in their Weaver scripts using the standard
        # Python import facilities.
        if self.import_builtins:
            self._import('abstraction', ABSTRACTIONS)
            self._import('dataset', DATASETS)
            self._import('function', FUNCTIONS)
            self._import('nest', NESTS)
            self._import('options', OPTIONS)
            self._import('stack', STACKS)

        # Execute nest
        with Nest(work_dir, wrapper=self.engine_wrapper) as nest:
            with self.options:
                try:
                    self.function(*self.arguments)
                    nest.compile()
                except Exception as e:
                    fatal(D_SCRIPT, 'Error compiling script: {0}'.format(e), print_traceback=True)

                if self.execute_dag:
                    debug(D_SCRIPT, 'Executing generated DAG {0} with {1}'.format(
                        nest.dag_path, nest.path))
                    nest.execute(self.engine_arguments, exit_on_failure=True)

