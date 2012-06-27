#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# $Id$
#
"""Create environment variable symlinks.
"""
#
# Top-level definitions.
#
__author__ = 'Benjamin Weaver <benjamin.weaver@nyu.edu>'
__version__ = '$Revision$'.split(': ')[1].split()[0]
__all__ = [ ]
__docformat__ = 'restructuredtext en'
#
# Modules
#
import argparse
from collections import OrderedDict
import ConfigParser
import glob
import os
import os.path
import sys
#
# parse_cfg()
#
def parse_cfg(cfg,root):
    """Parse a tree configuration file.

    Parameters
    ----------
    cfg : ConfigParser.ConfigParser
        A ``ConfigParser`` object.
    root : str
        The value of ``$SAS_ROOT``.

    Returns
    -------
    env : collections.OrderedDict
        A mapping containing all the configuration file data
    """
    env = OrderedDict()
    replace = '@FILESYSTEM@'
    env['default'] = cfg.defaults()
    if env['default']['FILESYSTEM'] == replace:
        env['default']['FILESYSTEM'] = root
    # env['default']['install'] = os.path.dirname(os.path.dirname(os.getenv('INSTALL_DIR')))
    env['default']['current'] = env['default']['current'] == 'True'
    for sec in cfg.sections():
        env[sec] = OrderedDict()
        for opt in cfg.options(sec):
            if opt in env['default']:
                continue
            val = cfg.get(sec,opt)
            if val.find(replace) == 0:
                val = val.replace(replace,root)
            env[sec][opt] = val
    return env
#
#
#
def make_link(src,link,options):
    """Encapsulate link creation
    """
    debug = options.test or options.verbose
    if debug:
        print("{0} -> {1}".format(link,src))
    if not options.test:
        if os.path.islink(link):
            os.remove(link)
        os.symlink(src,link)
    return
#
# Main function
#
def main():
    """Program to run if called as an executable."""
    #
    # Get options
    #
    parser = argparse.ArgumentParser(description=__doc__,prog=os.path.basename(sys.argv[0]))
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
        help='Print extra information.')
    parser.add_argument('-f', '--force', action='store_true', dest='force',
        help='Force the creation of some symlinks.')
    parser.add_argument('-t', '--test', action='store_true', dest='test',
        help='Only show what would be done (implies --verbose).')
    parser.add_argument('-o', '--only', action='store', dest='only',
        default='ALL', metavar='TREE',
        help='Create links for only TREE.')
    parser.add_argument('-r', '--root', action='store', dest='root',
        default=os.path.dirname(os.getenv('SAS_ROOT')),
        help='Override the value of $SAS_ROOT.',metavar='DIR')
    options = parser.parse_args()
    debug = options.test or options.verbose
    #
    # Find the data directory
    #
    datadir = os.path.join(os.getenv('TREE_DIR'),'data')
    if not os.path.exists(datadir):
        datadir = os.path.join('..','data')
        if not os.path.exists(datadir):
            print("Could not find a data directory!")
            sys.exit(1)
    #
    # Set up readme file
    #
    readme = """<p>This directory contains links to the contents of
environment variables defined by the tree product, version {0}.
To examine the <em>types</em> of files contained in each environment variable
directory, visit <a href="http://{1}.sdss3.org/datamodel/files/">the datamodel.</a></p>
"""
    #
    # Read the configuration files
    #
    for cfgfile in glob.glob(os.path.join(datadir,'*.cfg')):
        cfg = ConfigParser.SafeConfigParser()
        cfg.optionxform = str
        cfg.read(cfgfile)
        env = parse_cfg(cfg,options.root)
        if options.only != 'ALL' and env['default']['name'] != options.only:
            continue
        # if debug:
        #     print(env)
        if os.path.exists(env['general']['SAS_ROOT']):
            if debug:
                print("Found {0}.".format(env['general']['SAS_ROOT']))
            envdir = os.path.join(env['general']['SAS_ROOT'],'env')
            if not os.path.exists(envdir):
                if debug:
                    print("Creating {0}.".format(envdir))
                if not options.test:
                    os.mkdir(envdir)
            readmefile = os.path.join(envdir,'README.html')
            if not os.path.exists(readmefile):
                if env['general']['SAS_ROOT'].find('/mount/coma1') == 0:
                    url = 'mirror'
                else:
                    url = 'data'
                if debug:
                    print("Creating {0}.".format(readmefile))
                if not options.test:
                    with open(readmefile,'w') as f:
                        f.write(readme.format(env['default']['name'],url))
            for section in env:
                if section == 'default':
                    continue
                for var in env[section]:
                    if var.find('_ROOT') > 0:
                        continue
                    src = env[section][var]
                    link = os.path.join(envdir,var)
                    if section == 'general' and var in ('CAS_LOAD','STAGING_DATA'):
                        #
                        # For this section only, install links only if their
                        # targets exist. The --force option overrides this.
                        #
                        if options.force or os.path.exists(src):
                            make_link(src,link,options)
                    else:
                        make_link(src,link,options)
        else:
            print("{0} doesn't exist, skipping env link creation.".format(env['general']['SAS_ROOT']))
    return
#
#
#
if __name__ == '__main__':
    main()

