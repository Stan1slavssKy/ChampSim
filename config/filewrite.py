#    Copyright 2023 The ChampSim Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import difflib
import hashlib
import itertools
import operator
import os
import json
import pathlib

from .makefile import get_makefile_lines
from .instantiation_file import get_instantiation_lines
from .instantiation_file import get_instantiation_header
from . import util

warning_text = (
'THIS FILE IS AUTOMATICALLY GENERATED',
'Do not edit this file. It will be overwritten when the configure script is run.',
)

def contextualize_warning(prefix, line_prefix, suffix):
    ''' Generate a warning contextualized with the given comment aspects. '''
    return (prefix, *(f' {line_prefix} {l}' for l in warning_text), suffix, '')

def cxx_generated_warning():
    ''' Generate a warning commented in a C++ style. '''
    return contextualize_warning('/***', '*', '***/')

def make_generated_warning():
    ''' Generate a warning commented in a Make style. '''
    return contextualize_warning('###', '#', '###')

def cxx_file(lines):
    ''' Generate a C++ file, with a warning header. '''
    yield from cxx_generated_warning()
    yield from lines

def files_are_different(rfp, new_rfp, verbose=False):
    ''' Determine if the two files are different, excluding whitespace at the beginning or end of lines '''
    old_file_lines = list(l.strip() for l in rfp)
    new_file_lines = list(l.strip() for l in new_rfp)
    diff = difflib.SequenceMatcher(a=old_file_lines, b=new_file_lines).ratio()
    if verbose:
        print('File difference:', diff)
    return diff < 1

def write_if_different(fname, new_file_string, file=None, verbose=False):
    '''
    Write to a file if and only if it differs from an existing file with the same name.

    :param fname: the name of the destination file
    :param new_file_string: the desired contents of the file
    '''
    should_write = True
    if os.path.exists(fname):
        with open(fname, 'rt') as rfp:
            should_write = files_are_different(rfp, new_file_string.splitlines())

    if should_write:
        if verbose:
            print("Writing file", fname)

        if file is None:
            os.makedirs(os.path.abspath(os.path.dirname(fname)), exist_ok=True)
            with open(fname, 'wt') as wfp:
                wfp.write(new_file_string)
        else:
            file.write(new_file_string)

def try_int(val):
    '''
    Attempt to convert the value to a Python standard int.
    For use with json.dump().
    '''
    try:
        return int(val)
    except Exception as exc:
        raise TypeError from exc

class Fragment:
    '''
    Examines the given config and prepares to write the needed files.

    Programs may use this class for fine-grained control of when and how files are written.
    '''
    @staticmethod
    def __part_joiner(iterable):
        it = iter(iterable)
        key, first_value = next(it)

        header_len = 0
        if os.path.splitext(key)[1] in ('.cc', '.h', '.inc'):
            header_len = len(cxx_generated_warning())
        if os.path.splitext(key)[1] in ('.mk',):
            header_len = len(make_generated_warning())

        contents_parts = (itertools.islice(v[1], header_len, None) for v in it)
        return key, tuple(itertools.chain(first_value, *contents_parts))

    def __init__(self, fileparts=None):
        self.fileparts = list(fileparts or [])

    @staticmethod
    def join(*frags):
        ''' Merge multiple Fragments into one. '''
        joined_parts = list(itertools.chain(*(f.file_parts() for f in frags)))
        fileparts = list(util.collect(joined_parts, operator.itemgetter(0), Fragment.__part_joiner))
        return Fragment(fileparts)

    @staticmethod
    def from_config(parsed_config, bindir_name=None, srcdir_names=None, objdir_name=None, makedir_name=None, verbose=False):
        '''
        Produce a sequence of Fragments from the result of parse.parse_config().

        :param parsed_config: the result of parsing a configuration file
        :param bindir_name: the directory in which to place the binaries
        :param srcdir_name: the directory to search for source files
        :param objdir_name: the directory to place object files
        :param makedir_name: the directory to place makefiles
        '''
        champsim_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bindir_name = bindir_name or os.path.join(champsim_root, 'bin')
        srcdir_names = srcdir_names or []
        objdir_name = objdir_name or os.path.join(champsim_root, '.csconfig')
        makedir_name = makedir_name or champsim_root

        if verbose:
            print('Configuring files to:')
            print('Binary directory:', bindir_name)
            print('Source directory:', srcdir_names)
            print('Object directory:', objdir_name)
            print('Makefile directory:', makedir_name)

        build_id = hashlib.shake_128(json.dumps(parsed_config, sort_keys=True, default=try_int).encode('utf-8')).hexdigest(8)

        executable_basename, elements, modules_to_compile, module_info, config_file = parsed_config

        joined_module_info = util.subdict(util.chain(*module_info.values()), modules_to_compile) # remove module type tag
        executable = os.path.join(bindir_name, executable_basename)
        if verbose:
            print('For Executable', executable)
            print('Modules:')
            for module in joined_module_info.values():
                print(f'  {module["name"]}: {module["path"]} -> {module["class"]}')
            print('Writing objects to', objdir_name)

        # Touch 'path/to/__legacy__' to ensure makefile will generate legacy files
        for legacy_marker in (pathlib.Path(module['path'], '__legacy__') for module in joined_module_info.values() if module.get('legacy')):
            if verbose:
                print('Touching file:', str(legacy_marker))
            legacy_marker.touch()

        fileparts = [
            # Instantiation file
            (os.path.join(objdir_name, 'core_inst.inc'), cxx_file(get_instantiation_header(len(elements['cores']), config_file, build_id=build_id))),
            (os.path.join(objdir_name, 'core_inst.cc.inc'), cxx_file(get_instantiation_lines(build_id=build_id, **elements))),

            # Makefile generation
            (os.path.join(makedir_name, '_configuration.mk'), (
                *make_generated_warning(),
                *get_makefile_lines(build_id, executable, joined_module_info)
            ))
        ]
        return Fragment(list(util.collect(fileparts, operator.itemgetter(0), Fragment.__part_joiner))) # hoist the parts

    def write(self, verbose=False):
        ''' Write the internal series of fragments to file. '''
        for fname, fcontents in self.fileparts:
            write_if_different(fname, '\n'.join(l.rstrip() for l in fcontents), verbose=verbose)

    def file_parts(self):
        return self.fileparts

    def __iter__(self):
        return iter(self.file_parts())

class FileWriter:
    '''
    This class maintains the state of one or more configurations to be written.

    This class provides a context manager interface over a set of Fragments, and is more convenient for general use.

    :param bindir_name: The default directory for binaries if none is given to write_files().
    :param objdir_name: The default directory for object files if none is given to write_files().
    '''
    def __init__(self, bindir_name=None, objdir_name=None, makedir_name=None, verbose=False):
        self.fragments = []
        self.bindir_name = bindir_name
        self.objdir_name = objdir_name
        self.makedir_name = makedir_name
        self.verbose = verbose

    def __enter__(self):
        ''' This function forms one half of the context manager interface '''
        self.fragments = []
        return self

    def write_files(self, parsed_config, bindir_name=None, srcdir_names=None, objdir_name=None, makedir_name=None):
        '''
        Accumulate the results of parsing a configuration into the File Writer.
        Parameters passed here will override parameters given in the constructor

        :param parsed_config: the result of parsing a configuration file
        :param bindir_name: the directory in which to place the binaries
        :param srcdir_name: the directory to search for source files
        :param objdir_name: the directory to place object files
        '''
        self.fragments.append(Fragment.from_config(
            parsed_config,
            bindir_name=bindir_name or self.bindir_name,
            srcdir_names=srcdir_names or [],
            objdir_name=os.path.abspath(objdir_name or self.objdir_name),
            makedir_name=makedir_name or self.makedir_name,
            verbose=self.verbose
        ))

    @staticmethod
    def write_fragments(*fragments):
        ''' Write out a set of prepared fragments. '''
        if not fragments:
            return
        Fragment.join(*fragments).write()

    def finish(self):
        ''' Write all accumulated configurations to their files. '''
        FileWriter.write_fragments(*self.fragments)

    def __exit__(self, exc_type, exc_value, traceback):
        ''' This function terminates the context manager and calls :meth:`finish()`. '''
        if exc_type is None:
            self.finish()
