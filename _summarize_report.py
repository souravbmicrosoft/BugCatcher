import json
p = r"C:\Users\souravb\OneDrive - Microsoft\Documents\Hackathon\Hackathon'25\PRAnalyzer\Code\report_azure.json"
with open(p, 'r', encoding='utf-8') as f:
    j = json.load(f)

total = len(j)
match_found = sum(1 for e in j if e.get('match', {}).get('found'))
candidates = sum(1 for e in j if e.get('candidates'))
pr_matches = sum(len(e.get('pr_matches', [])) for e in j)
fixes = sum(len(e.get('fixes', [])) for e in j)
print(f"total_frames={total}, matched_snippets={match_found}, frames_with_candidates={candidates}, pr_matches={pr_matches}, total_fix_suggestions={fixes}")

count = 0
for e in j:
    notable = e.get('match', {}).get('found') or e.get('candidates') or e.get('fixes')
    if notable:
        print('\n--- FRAME ---')
        print('raw:', e['frame'].get('raw'))
        if e.get('match', {}).get('found'):
            print('matched path:', e['match'].get('path'))
            print('line:', e['match'].get('line'))
            snippet = e['match'].get('snippet','')
            print('snippet preview:')
            for ln in snippet.splitlines()[:4]:
                print('  ', ln)
        if e.get('candidates'):
            print('candidates sample:', e['candidates'][:4])
        if e.get('pr_matches'):
            print('pr_matches:', e['pr_matches'])
        if e.get('fixes'):
            print('fixes:', e['fixes'])
        count += 1
        if count >= 8:
            break
