#!/usr/bin/env python3
"""Script to replace print statements with logger calls in rag_service.py"""

import re

input_file = "app/services/rag_service.py"
output_file = "app/services/rag_service.py"

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace print statements with appropriate logger calls
replacements = [
    # DEBUG statements -> logger.debug
    (r'print\(f"DEBUG:', r'logger.debug(f"'),
    (r'print\("DEBUG:', r'logger.debug("'),
    
    # Error indicators
    (r'print\(f"❌', r'logger.error(f"❌'),
    (r'print\(f"Error ', r'logger.error(f"Error '),
    (r'print\(f"Indexing error', r'logger.error(f"Indexing error'),
    (r'print\(f"LLM Invocation Error', r'logger.error(f"LLM Invocation Error'),
    (r'print\(f"Classification parsing failed', r'logger.error(f"Classification parsing failed'),
    
    # Warning indicators
    (r'print\(f"⚠️', r'logger.warning(f"⚠️'),
    (r'print\("⚠️', r'logger.warning("⚠️'),
    (r'print\(f"No chunks found', r'logger.warning(f"No chunks found'),
    
    # Info indicators
    (r'print\(f"✅', r'logger.info(f"✅'),
    (r'print\(f"🔍', r'logger.info(f"🔍'),
    (r'print\(f"📦', r'logger.info(f"📦'),
    (r'print\(f"🔎', r'logger.info(f"🔎'),
    (r'print\(f"Deleted ', r'logger.info(f"Deleted '),
    (r'print\(f"No more documents', r'logger.info(f"No more documents'),
    
    # Multi-line print (special case)
    (r'print\(\s+f"DEBUG: Retrieval failed', r'logger.info(f"DEBUG: Retrieval failed'),
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Write back
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Replaced print statements in {output_file}")
