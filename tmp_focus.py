from pr_analyzer import analyzer, retriever, parser, llm
index_path='.\demo_index'
trace=open('sample_trace.txt').read()
frames=parser.parse_stack_trace(trace)
frame=frames[0]
# retrieve top 12 snippets but prefer exact file
snips=retriever.retrieve_for_frame(index_path, frame['raw'], top_k=12)
# Filter to local BaseFiniteStateMachineContext.cs snippets first
local=[s for s in snips if 'BaseFiniteStateMachineContext.cs' in s['path']]
if local:
    ordered = local + [s for s in snips if s not in local]
else:
    ordered = snips
print('Using', len(ordered), 'snippets;', len(local), 'are local BaseFiniteStateMachineContext.cs')
# Build prompt manually and call LLM
prompt=analyzer._build_prompt(frame, ordered[:8])
print('Prompt built; calling LLM...')
resp=llm.ask_llm(prompt, temperature=0.2)
print('\nLLM raw response:\n', resp)
