import tempfile
import subprocess32
import os
import signal
import time
import select
import re


def write_case_to_file(case):
    """Given a case, write it to a temporary file for consumption by the fuzzed program, and return the file path"""
    
    handle = tempfile.NamedTemporaryFile(delete=False)
    path = handle.name
    handle.write(case)
    handle.close()
    
    return path


def execute(args, case, timeout = 3):
    """Executes the program to be fuzzed (automatically saving case to file as needed),
    and returns a dictionary of the data collected from the run (exit code, stdout, stderr, duration)"""
    
    ret = -1
    out = ''
    err = ''
    runtime = -1
    
    args = list(args)
    case = bytes(case)
    
    needs_file = False
    
    if '@@' in args:
        # The program takes input from a file, not STDIN
        
        needs_file = True
        path = write_case_to_file(case)
        
        file_arg_idx = args.index('@@')
        args[file_arg_idx] = path
    
    
    start = time.time()
    
    proc = subprocess32.Popen(args, stdin=subprocess32.PIPE, stdout=subprocess32.PIPE, stderr=subprocess32.PIPE)
    try:
        out, err = proc.communicate(input=None if needs_file else case, timeout=timeout)
        ret = proc.poll()
        runtime = time.time() - start
    except subprocess32.TimeoutExpired:
        os.kill(proc.pid, signal.SIGKILL)
        ret = -1
    except select.error:
        print 'Unknown error while executing. Disregarding result.'
        os.kill(proc.pid, signal.SIGKILL)
        ret = -1
    
    if needs_file:
        os.remove(path)
    
    return {'return': ret, 'stdout': out, 'stderr': err, 'runtime': runtime}


def is_unusual(baseline, run, override_regexs = [], ignore = ['stderr']):
    """Given a baseline series of statistics, try and determine if this run is different"""
    
    for r in override_regexs:
        if ('stdout' not in ignore and re.search(r, run['stdout'])) or ('stderr' not in ignore and re.search(r, run['stderr'])):
            return True, 'regex match'
    if 'timeout' not in ignore and run['return'] == -1:
        return True, 'timeout'
    if 'return' not in ignore and run['return'] != -1 and run['return'] != baseline['return']:
        return True, 'return ({})'.format(run['return'])
    if 'runtime' not in ignore and (run['runtime'] < baseline['runtime']-1 or run['runtime'] > baseline['runtime']+1):
        return True, 'runtime'
    if 'stderr' not in ignore:
        from difflib import SequenceMatcher
        
        matcher = SequenceMatcher(lambda x: x in " \r\n\t", run['stderr'], baseline['stderr'])
        if matcher.ratio() < 0.6:
            return True, 'stderr'
    
    return False, None