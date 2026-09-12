import pathlib
p = pathlib.Path('app/agents/intents.py')
lines = p.read_text(encoding='utf-8').splitlines()

def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return -1

# 1. Fix _contrastive_score: text.count() -> whitespace-split count
start = find_line('def _contrastive_score')
if start != -1:
    for i in range(start, len(lines)):
        if 'return text.lower().count' in lines[i] or 'return text.count' in lines[i]:
            # Replace with tokenize-based count
            indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            lines[i] = indent + '    return _tokenize(normalized).count(token)\n'
            print(f'Fixed _contrastive_score at line {i+1}')
            break

# 2. Fix _score_phrase: re.findall -> tokenize
start = find_line('def _score_phrase')
if start != -1:
    for i in range(start, len(lines)):
        if 're.findall' in lines[i] and 'r' + chr(34) + '\S+' in lines[i]:
            indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            lines[i] = indent + '    query_tokens = _tokenize(normalized)\n'
            print(f'Fixed _score_phrase re.findall at line {i+1}')
            break
    # Fix the next line (match loop)
    for i in range(start, len(lines)):
        if 'for token in query_tokens' in lines[i]:
            lines[i] = '            if _tokens_match(token, p_tokens):' + '\n'
            print(f'Fixed _score_phrase loop at line {i+1}')
            break

# 3. Replace _contains(normalized, ...) calls in classify() with _matches_any
#    Find each occurrence
for i in range(len(lines)):
    stripped = lines[i].strip()
    if stripped.startswith('_contains(normalized, _PRICE'):
        lines[i] = lines[i].replace('_contains(normalized,', '_matches_any(') + '\n'
        print(f'Replaced _contains->_matches_any at line {i+1}')
    elif stripped.startswith('_contains(normalized, _VALUATION'):
        lines[i] = lines[i].replace('_contains(normalized,', '_matches_any(') + '\n'
        print(f'Replaced _contains->_matches_any at line {i+1}')
    elif stripped.startswith('_contains(normalized, _HEALTH'):
        lines[i] = lines[i].replace('_contains(normalized,', '_matches_any(') + '\n'
        print(f'Replaced _contains->_matches_any at line {i+1}')
    elif stripped.startswith('_contains(normalized, _RISK'):
        lines[i] = lines[i].replace('_contains(normalized,', '_matches_any(') + '\n'
        print(f'Replaced _contains->_matches_any at line {i+1}')

p.write_text('\n'.join(lines), encoding='utf-8')
print(f'Written {len(lines)} lines')
