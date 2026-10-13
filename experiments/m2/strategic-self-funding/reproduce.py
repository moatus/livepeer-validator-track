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
    import build
    run=build.build_profiles(args.core_only)
    if not args.core_only:
        import timelines,evidence
        extra=timelines.build(run)
        extra.update(evidence.build())
        from adapter import load_json,write_json
        import hashlib
        out=f.HERE/'generated/full';manifest=load_json(out/'manifest.json')
        manifest['counts'].update(extra);manifest['stage']='full'
        manifest['file_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'}
        write_json(out/'manifest.json',manifest)
    import verify
    verify.verify(args.core_only)
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
    print('PASS '+('core-only69 profiles' if args.core_only else 'full135 profiles/10 timelines/7 existing-evidence scope mappings')+'; original EX-03–07 verifiers pass. No owner research acceptance inferred.')


if __name__=='__main__':
    main()
