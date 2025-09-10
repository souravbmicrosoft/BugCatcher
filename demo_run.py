import os
import json
import sys

# Demo runner for PRAnalyzer using test-mode embeddings and a fake LLM
# Usage: python demo_run.py <repo_path> <index_path> <stack_trace_file>

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python demo_run.py <repo_path> <index_path> <stack_trace_file>')
        sys.exit(2)
    repo = sys.argv[1]
    index_path = sys.argv[2]
    trace_file = sys.argv[3]

    with open(trace_file, 'r', encoding='utf-8') as fh:
        stack_trace = fh.read()

    os.environ['PR_ANALYZER_UNIT_TEST'] = '1'

    from pr_analyzer.indexer import build_index
    import pr_analyzer.llm as llm
    from pr_analyzer.analyzer import analyze_stack_trace

    # fake LLM that returns a JSON analysis
    def fake_ask(prompt, temperature=0.0):
        # Small heuristic: if 'FiniteStateMachine' in prompt, mark as code
        classification = 'unknown'
        confidence = 0.5
        explanation = 'Could not determine.'
        suggested_fix = 'Inspect state transitions.'
        if 'FiniteStateMachine' in prompt or 'FiniteStateMachine' in stack_trace:
            classification = 'code'
            confidence = 0.88
            explanation = 'State machine transition attempted an invalid action outcome; likely missing guard or invalid state prior to transition.'
            suggested_fix = 'Add guard checks and validate action outcomes before state change; examine the method at the reported file and line.'
        return json.dumps({
            'classification': classification,
            'confidence': confidence,
            'explanation': explanation,
            'suggested_fix': suggested_fix,
        })

    # use real LLM if credentials are present (OPENAI_API_KEY or Azure vars)
    if os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_BASE'):
        print('Using real OpenAI/Azure LLM (credentials found)')
    else:
        print('No LLM credentials found; using fake LLM for demo')
        llm.ask_llm = fake_ask

    print('Indexing repository (test-mode embeddings) ...')
    build_index(repo, index_path)

    print('\nRunning analysis...')
    res = analyze_stack_trace(stack_trace, index_path, top_k=3)
    print(json.dumps(res, indent=2))
