import argparse
import os
import shlex
import time
import random

import mutate
import fuzzer

def main():
    parser = argparse.ArgumentParser(description='Test fuzzer')
    parser.add_argument('-b', '--base_dir', required=True, metavar='base case dir', type=str,
                       help='Directory with base cases')
    parser.add_argument('-o', '--out_dir', required=True, metavar='output dir', type=str,
                       help='Directory to put findings in')
    parser.add_argument('--regexs', metavar='regex file', type=str,
                       help='File which contains regexs which automatically mark a run as unusual')
    parser.add_argument('command', type=str,
                       help='The program to fuzz. Use @@ in the command if program reads file')

    args = parser.parse_args()

    command = shlex.split(args.command)
    
    regexs = []
    
    if not os.path.isdir(args.base_dir):
        raise ValueError('Base directory doesn\'t exist')
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
    if args.regexs:
        if not os.path.exists(args.regexs):
            raise ValueError('Regexs file doesn\'t exist')
        regexs = open(args.regexs, 'r').read().split('\n')

    print 'Fuzzing "{}" with command line arguments: {}'.format(command[0], command[1:])

    base_files = [x for x in os.listdir(args.base_dir) if x[0] != '.']

    print 'Starting with base files: {}'.format(base_files)
    print ''

    # Run against base cases to get return code, expected output, runtime, and other heuristics

    base_runs = {}

    for filename in base_files:
        print 'Testing {}'.format(filename)
        with open(os.path.join(args.base_dir, filename), 'r') as file:
            contents = file.read()
            run = fuzzer.execute(command, contents)
            if run['return'] != -1:
                base_runs[filename] = run
                base_runs[filename]['contents'] = contents
            else:
                raise Exception('Failure running base case.')

    print ''

    def get_baseline_measurement(runs, measurement):
        vals = [runs[fn][measurement] for fn in runs.keys()]
        return round(float(sum(vals)) / len(vals), 1)

    baseline = {}
    baseline['return'] = int(get_baseline_measurement(base_runs, 'return'))
    baseline['runtime'] = get_baseline_measurement(base_runs, 'runtime')

    # Just use the first base case's std(out,err) for our "baseline"
    baseline['stdout'] = base_runs[base_files[0]]['stdout']
    baseline['stderr'] = base_runs[base_files[0]]['stderr']

    print 'Got baseline statistics:'
    for k in baseline.keys():
        print '{}:  {}'.format(k, str(repr(baseline[k]))[:50])

    print ''
    print 'Checking for irregularities within base cases...'

    for filename in base_files:
        weird, cause = fuzzer.is_unusual(baseline, base_runs[filename])
        if weird:
            print 'Base case "{}" is unusual due to its {}'.format(filename, cause)

    print ''
    print 'Beginning fuzzing'
    print ''

    # Random mutations

    for i in range(10000):    
        base = base_runs[random.choice(base_runs.keys())]
    
        mutated = mutate.random_replace(base['contents'], n_mutations = 10)
    
        run = fuzzer.execute(command, mutated)
    
        weird, cause = fuzzer.is_unusual(baseline, run, override_regexs=regexs, ignore=['stderr', 'timeout', 'runtime'])
        if weird:
            print 'Mutated case is unusual due to its {}'.format(cause)
        
            save_name = 'run{}'.format(i)

            print 'Saving to {} in the output directory'.format(save_name)
        
            f = open(os.path.join(args.out_dir, save_name), 'wb')
            f.write(mutated)
            f.close()

if __name__ == '__main__':
    main()