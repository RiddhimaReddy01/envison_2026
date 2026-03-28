import re

with open('data_ingestion.py', encoding='utf-8') as f:
    content = f.read()

# Replace all non-ASCII characters
content = content.encode('ascii', errors='replace').decode('ascii')
# Clean up the replacement marker
content = content.replace('?', '?')  # keep ? as-is, they're readable

with open('data_ingestion.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done — all non-ASCII replaced with '?'")
