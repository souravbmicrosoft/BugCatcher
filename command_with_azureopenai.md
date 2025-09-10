$env:AZURE_OPENAI_ENDPOINT = 'https://pranalyzer.openai.azure.com'
$env:AZURE_OPENAI_KEY = 'D7pfxKxz9TsVnXac4hkW1QdjlkfGqOBZEo04wg7IHdPUls1PPO4rJQQJ99BIACYeBjFXJ3w3AAABACOGlwYT'
$env:AZURE_OPENAI_DEPLOYMENT = 'gpt-4.1-mini'
python diagnose_trace.py --repo "Q:\src\DsMainDev\Sql\xdb" --trace "C:\Users\souravb\OneDrive - Microsoft\Documents\Hackathon\Hackathon'25\PRAnalyzer\Code\sample_trace.txt" --out "C:\Users\souravb\OneDrive - Microsoft\Documents\Hackathon\Hackathon'25\PRAnalyzer\Code\report_azure.json" --since 30 --context 6 --use-llm