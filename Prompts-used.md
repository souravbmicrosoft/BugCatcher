Prompts used:

1. Hi Copilot you are a Senior Staff Engineer and need to solve the problem mentioned below.I want to build a product where I want to figure out issues in the code based on stack trace available from the telemetry. Where the LLM model should be able to understand the codebase and has access to it and whenever a stack trace is given it would be able to figure if the issue is related to code or any external dependency and then would be able to suggest what is the issue in the code.You are allowed to use Azure AI Foundry or custom python code use any available LLM model. write an end to end working code that actually works in production and not just a prototype.

This is the code repo path that I have locally available.

2. Plan looks good, go ahead and continue
3. Create venv and install all the required libraries and then continue ahead
4. Getting error:
Getting error
ERROR: Could not find a version that satisfies the requirement faiss-cpu==1.8.3 (from versions: 1.7.3, 1.7.4, 1.8.0, 1.8.0.post1, 1.9.0, 1.9.0.post1, 1.10.0, 1.11.0, 1.11.0.post1, 1.12.0)
ERROR: No matching distribution found for faiss-cpu==1.8.3

5. Python version Python 3.11.9
6. Continue with the indexer
7. Adding to this problem statement, based on the stack trace and code files find all the PRs that were raised in last 1 month for those specific suspected files and then find if any PR is culprit for the issue.

If none of the PR is culprit classify it as an issue not related to code changes.

This improvements should be part of the python code. Don't do extensive search to all PRs rather look for limited number of PRs based on probability.