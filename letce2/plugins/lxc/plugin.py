# Copyright (c) 2017-2018 - Adjacent Link LLC, Bridgewater, New Jersey
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
# * Neither the name of Adjacent Link LLC nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# See toplevel COPYING for more information.

from __future__ import absolute_import, division, print_function

import sys
import os
import subprocess
import re

from letce2.utils.filesystem import mkdir_p
from letce2.interface.plugin import Plugin as PluginBase
from letce2.engine.build import *

class Plugin(PluginBase):
    def __init__(self,name,argumnet_parser):
        lxc_subparser = argumnet_parser.add_parser(name,
                                                   help='executes LXC node experiments.')

        subparsers = lxc_subparser.add_subparsers(help='{} sub-command help'.format(name))


        subparser_build = subparsers.add_parser('build',
                                                help='create all experiment input files.')

        subparser_build.add_argument('experiment-config',
                                     nargs='+',
                                     type=str,
                                     help='configuration file.')

        subparser_build.add_argument('--lock-file',
                                     type=str,
                                     metavar='FILE',
                                     default='/var/run/lock/letce.lock',
                                     help='lock file.')

        subparser_build.add_argument('--force',
                                     action='store_true',
                                     help='ignore present lock file [default: %(default)s].')

        subparser_build.set_defaults(plugin_subcommand='build')

        subparser_start = subparsers.add_parser('start',
                                               help='start the experiment.')
        subparser_start.add_argument('-e',
                                     '--environment',
                                     type=str,
                                     metavar='FILE',
                                     default='',
                                     help='environment file to source.')

        subparser_start.add_argument('--scenario-delay',
                                     type=int,
                                     metavar='SECONDS',
                                     default=20,
                                     help='delay scenario for specified seconds [default: %(default)s].')

        subparser_start.add_argument('--lock-file',
                                     type=str,
                                     metavar='FILE',
                                     default='/var/run/lock/letce.lock',
                                     help='lock file.')

        subparser_start.add_argument('--force',
                                     action='store_true',
                                     help='ignore present lock file [default: %(default)s].')

        subparser_start.set_defaults(plugin_subcommand='start')

        subparser_stop = subparsers.add_parser('stop',
                                               help='stop the experiment.')

        subparser_stop.add_argument('-e',
                                    '--environment',
                                    type=str,
                                    metavar='FILE',
                                    default='',
                                    help='environment file to source.')

        subparser_stop.add_argument('--lock-file',
                                    type=str,
                                    metavar='FILE',
                                    default='/var/run/lock/letce.lock',
                                    help='lock file.')

        subparser_stop.add_argument('--force',
                                    action='store_true',
                                    help='ignore missing lock file [default: %(default)s].')

        subparser_stop.set_defaults(plugin_subcommand='stop')


        subparser_clean = subparsers.add_parser('clean',
                                                help='delete all conifugration input and experiment output files.')

        subparser_clean.set_defaults(plugin_subcommand='clean')

        subparser_clean.add_argument('--lock-file',
                                     type=str,
                                     metavar='FILE',
                                     default='/var/run/lock/letce.lock',
                                     help='lock file.')

        subparser_clean.add_argument('--force',
                                     action='store_true',
                                     help='ignore missing lock file [default: %(default)s].')

        lxc_subparser.set_defaults(subcommand=name)

    def process(self,nodes_include,nodes_exclude,args):
        if args['plugin_subcommand'] == 'build':
            self._do_build(args)

        elif args['plugin_subcommand'] == 'start':
            self._do_start(nodes_include,args)

        elif  args['plugin_subcommand'] == 'stop':
            self._do_stop(nodes_include,args)

        elif  args['plugin_subcommand'] == 'clean':
            self._do_clean(nodes_include,nodes_exclude,args)

    def _do_build(self,args):
        if os.path.exists(args['lock_file']) and not args['force']:
            print('lock file found:', args['lock_file'], file=sys.stderr)
            print('Run `letce2 lxc stop` before continuing or \'--force\' to ignore.',file=sys.stderr)
            exit(1)

        nodes = build_configuration(args['experiment-config'],
                                    args['include_filter'],
                                    args['exclude_filter'],
                                    args['include_file'],
                                    args['exclude_file'],
                                    args['manifest'],
                                    'letce2.plugins.lxc')

    def _do_start(self,nodes,args):
        if os.path.exists(args['lock_file']) and not args['force']:
            print('lock file found:', args['lock_file'], file=sys.stderr)
            print('Run `letce2 lxc stop` before continuing or \'--force\' to ignore.',file=sys.stderr)
            exit(1)

        subprocess.call(['sudo',
                         'rm',
                         '-rf',
                         'persist'])

        mkdir_p('persist/host/var/run')

        mkdir_p('persist/host/var/log')

        mkdir_p('persist/host/var/tmp')

        subprocess.call(['sudo',
                         'host/control',
                         'prestart',
                         os.getcwd(),
                         args['environment'],
                         str(args['scenario_delay'])])

        subprocess.call(['sudo',
                         'host/bridge',
                         'start'])

        # disable realtime scheduling contraints
        subprocess.call(['sudo',
                         'sysctl',
                         'kernel.sched_rt_runtime_us=-1'])

        for node in nodes:
            if node == 'host':
                continue

            mkdir_p('persist/%s/var/run' % node)

            mkdir_p('persist/%s/var/log' % node)

            mkdir_p('persist/%s/var/tmp' % node)

            subprocess.Popen(['sudo',
                              'lxc-execute',
                              '-f',
                              '%s/lxc.conf' % node,
                              '-n',
                              node,
                              '-o',
                              'persist/%s/var/log/lxc-execute.log' % node,
                              '--',
                              '%s/init' % node,
                              os.getcwd(),
                              node,
                              args['environment'],
                              str(args['scenario_delay'])])

        subprocess.call(['sudo',
                         'host/bridge',
                         'prep'])

        subprocess.call(['sudo',
                         'host/control',
                         'start',
                         os.getcwd(),
                         args['environment'],
                         str(args['scenario_delay'])])

        # touch lock file
        subprocess.call(['sudo',
                         'touch',
                         args['lock_file']])

    def _do_stop(self,nodes,args):
        if not os.path.exists(args['lock_file']) and not args['force']:
            print('lock file missing:', args['lock_file'],file=sys.stderr)
            print('Use \'--force\' to ignore and continue.',file=sys.stderr)
            exit(1)

        subprocess.call(['sudo',
                         'host/control',
                         'prestop',
                         os.getcwd(),
                         args['environment'],
                         ''])

        for node in nodes:
            subprocess.call(['sudo',
                             'lxc-stop',
                             '-n',
                             node])

        subprocess.call(['sudo',
                         'host/bridge',
                         'stop'])

        subprocess.call(['sudo',
                         'host/control',
                         'stop',
                         os.getcwd(),
                         args['environment'],
                         ''])

        if os.path.exists(args['lock_file']):
            subprocess.call(['sudo',
                             'rm',
                             '-f',
                             args['lock_file']])



    def _do_clean(self,nodes_include,nodes_exclude,args):
        if os.path.exists(args['lock_file']) and not args['force']:
            print('lock file found:', args['lock_file'], file=sys.stderr)
            print('Run `letce2 lxc stop` before continuing or \'--force\' to ignore.',file=sys.stderr)
            exit(1)

        clean_configuration(nodes_include,
                            args['manifest'])

        if not nodes_exclude:
            if os.path.isdir('persist'):
                subprocess.call(['sudo',
                                 'rm',
                                 '-rf',
                                 'persist'])
        else:
            for node in nodes_include:
                if os.path.isdir('persist/{}'.format(node)):
                    subprocess.call(['sudo',
                                     'rm',
                                     '-rf',
                                     'persist/{}'.format(node)])

                nodes_to_manifest(nodes_exclude,
                                  args['manifest'])
