import subprocess
import json
import re
from pathlib import Path

# Heuristic script:
# - given a repo path and list of suspect files, find merged PRs in last 30 days that touched those files or nearby directories
# - parse PR numbers from merge commit messages ("Merged PR 12345")
# - for each candidate PR, list files changed and check if suspect files appear or if changes are in nearby files (same folder or metadata builders)
# - produce a simple classification: 'culprit' if suspect file changed or enum/metadata-related files touched, else 'not-culprit'


def run_cmd(cmd, cwd=None):
    out = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{out.stderr}")
    return out.stdout


def parse_prs_from_log(repo_path, since='30 days'):
    # find merge commits in last 30 days
    cmd = f"git -C \"{repo_path}\" log --since=\"{since}\" --pretty=format:%H__%s"
    out = run_cmd(cmd)
    prs = []
    for line in out.splitlines():
        if 'Merged PR' in line:
            h, s = line.split('__', 1)
            m = re.search(r'Merged PR\s*(\d+)', s)
            pr = m.group(1) if m else None
            prs.append({'commit': h, 'subject': s.strip(), 'pr': pr})
    return prs


def files_changed_in_commit(repo_path, commit):
    cmd = f"git -C \"{repo_path}\" diff-tree --no-commit-id --name-only -r {commit}"
    out = run_cmd(cmd)
    files = [l.strip() for l in out.splitlines() if l.strip()]
    return files


def classify_pr(repo_path, pr_entry, suspects):
    commit = pr_entry['commit']
    files = files_changed_in_commit(repo_path, commit)
    # check exact suspect paths
    suspect_hits = [f for f in files if any(f.endswith(s) or (s in f) for s in suspects)]
    # also check same directories
    dirs = {str(Path(s).parent) for s in suspects}
    nearby_hits = [f for f in files if any(str(Path(f).parent).endswith(d) for d in dirs)]

    verdict = 'not-culprit'
    reason = []
    if suspect_hits:
        verdict = 'culprit'
        reason.append('suspect file changed')
    elif nearby_hits:
        # nearby changes may still be relevant; mark as 'possible'
        verdict = 'possible'
        reason.append('nearby files changed')

    return {
        'pr': pr_entry.get('pr'),
        'commit': commit,
        'subject': pr_entry.get('subject'),
        'files_changed_count': len(files),
        'suspect_hits': suspect_hits,
        'nearby_hits': nearby_hits,
        'verdict': verdict,
        'reason': reason,
    }


def find_culprits(repo_path, suspects, since='30 days', max_prs=50):
    prs = parse_prs_from_log(repo_path, since=since)
    # limit by max_prs
    prs = prs[:max_prs]
    results = []
    for p in prs:
        try:
            res = classify_pr(repo_path, p, suspects)
        except Exception as e:
            res = {'pr': p.get('pr'), 'commit': p.get('commit'), 'error': str(e)}
        results.append(res)
    # final classification
    culprits = [r for r in results if r.get('verdict') == 'culprit']
    final = 'culprit_found' if culprits else 'no_culprit_in_recent_prs'
    return {'final': final, 'candidates': results}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True)
    p.add_argument('--since', default='30 days')
    p.add_argument('--max-prs', type=int, default=50)
    args = p.parse_args()

    suspects = [
        'Sql/xdb/common/fsm/BaseFiniteStateMachineContext.cs',
        'Sql/xdb/common/fsm/Attributes/FSMTargetStatesAttribute.cs',
        'Sql/xdb/common/fsm/FiniteStateMachineContext.cs',
    ]

    out = find_culprits(args.repo, suspects, since=args.since, max_prs=args.max_prs)
    print(json.dumps(out, indent=2))
