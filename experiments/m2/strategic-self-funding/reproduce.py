#!/usr/bin/env python3
"""Repository-contained staged reproduction, standard library Python 3.10+."""
import argparse
import subprocess
import sys

import fixtures as f


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core-only',action='store_true',help='69 defined core/control/confirmation/native rows only')
    args=parser.parse_args()
    if not args.core_only:
        parser.error('Full-stage implementation is pending the explicit first-core review pass; run --core-only.')
    import build
    build.build_core()
    import verify
    verify.verify()
    commands=[
        'self-funded-return/build.py','self-funded-return/verify.py',
        'evidence-self-funded/verify.py',
        'october-reconciliation/build.py','october-reconciliation/verify.py',
        'evidence-capability-pricing/verify.py',
    ]
    logs=[]
    for script in commands:
        path=f.ROOT/'experiments/m2'/script
        result=subprocess.run([sys.executable,str(path)],cwd=f.ROOT,text=True,capture_output=True,check=True)
        last_line=result.stdout.strip().splitlines()[-1] if result.stdout.strip() else 'completed'
        print(f'{script}: {last_line}',flush=True)
        logs.append(dict(command='python3 experiments/m2/'+script,returncode=result.returncode,
                         stdout=result.stdout,stderr=result.stderr))
    from adapter import write_json
    write_json(f.HERE/'generated/acceptance-checks.json',logs)
    print('PASS core-only reproduction; EX-03–07 original verifiers pass. Supplements/timelines/evidence outcomes remain uncomputed.')


if __name__=='__main__':
    main()
