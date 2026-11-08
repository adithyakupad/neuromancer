"""Mission-only non-neural stage runner using the qualified shared deadline."""
import argparse
import json
from pathlib import Path
import sys
from neuromancer.supervisor import Deadline, supervise


def main():
    p=argparse.ArgumentParser();p.add_argument('configuration',type=Path);a=p.parse_args()
    config=json.loads(a.configuration.read_text())
    deadline=Deadline.after(config['budget_s'])
    result=supervise(config['commands'],Path(config['supervision_output']),deadline,
                     workers=config.get('workers',1))
    print(json.dumps(dict(status=result['status'],deadline_ns=result['deadline_ns'],
                         finished_ns=result['finished_ns'],cleanup_verified=result['cleanup_verified'])),flush=True)
    if result['status']!='COMPLETED':sys.exit(1)


if __name__=='__main__':main()
