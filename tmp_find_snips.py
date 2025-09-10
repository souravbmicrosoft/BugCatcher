from pr_analyzer.indexer import search_index
from pr_analyzer import analyzer, llm, parser
index_path='.'+'\\demo_index'
query='BaseFiniteStateMachineContext.cs'
print('Searching index for', query)
res=search_index(index_path, query, top_k=20)
print('Found', len(res), 'results')
for i,r in enumerate(res[:10]):
    print('\n--- RESULT', i, '---')
    print('path:', r['path'])
    print('chunk_index:', r['chunk_index'])
    print('snippet:\n', r['snippet'][:800].replace('\n','\\n'))

# If we have at least one, build prompt using top 6 and call LLM
if res:
    frame_raw = open('sample_trace.txt').read().splitlines()[1]
    frames = parser.parse_stack_trace('\n'.join([frame_raw]))
    frame = frames[0]
    snippets = res[:6]
    prompt = analyzer._build_prompt(frame, snippets)
    print('\nCalling LLM with local snippets...')
    resp = llm.ask_llm(prompt, temperature=0.2)
    print('\nLLM response:\n', resp)
else:
    print('No results to analyze')
