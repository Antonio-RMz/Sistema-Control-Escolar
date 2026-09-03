import sys
import os
import re

# Reconfigure stdout to use utf-8 if it isn't already
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def read_file(filepath, start_line=1, end_line=None):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        if end_line is None:
            end_line = total_lines
        else:
            end_line = min(int(end_line), total_lines)
            
        start_line = max(1, int(start_line))
        
        print(f"--- FILE: {filepath} ({start_line} to {end_line} of {total_lines} lines) ---")
        for i in range(start_line - 1, end_line):
            print(f"{i + 1}: {lines[i]}", end='')
    except Exception as e:
        print(f"Error reading file: {e}")

def replace_content(filepath, target_content_file, replacement_content_file):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        with open(target_content_file, 'r', encoding='utf-8') as f:
            target = f.read()
            
        with open(replacement_content_file, 'r', encoding='utf-8') as f:
            replacement = f.read()
            
        if target not in content:
            print("ERROR: Target content not found in file.")
            # Let's do a fuzzy search or check why
            # Strip both and check
            if target.strip() in content.strip():
                print("WARNING: Found target content with slightly different whitespace. Performing exact replace on trimmed content is not supported yet.")
            return False
            
        occurrences = content.count(target)
        if occurrences > 1:
            print(f"WARNING: Target content found {occurrences} times. All will be replaced.")
            
        new_content = content.replace(target, replacement)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("SUCCESS: Replacement completed successfully.")
        return True
    except Exception as e:
        print(f"Error replacing content: {e}")
        return False

def search_text(path, query, extension=None):
    query_re = re.compile(query, re.IGNORECASE)
    if os.path.isfile(path):
        search_in_file(path, query_re)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if extension and not file.endswith(extension):
                    continue
                filepath = os.path.join(root, file)
                search_in_file(filepath, query_re)

def search_in_file(filepath, query_re):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f):
                if query_re.search(line):
                    print(f"{filepath}:{i+1}: {line.strip()}")
    except Exception:
        pass

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python file_utils.py read <filepath> [start_line] [end_line]")
        print("  python file_utils.py search <dir_or_file> <query> [extension]")
        print("  python file_utils.py replace <filepath> <target_file> <replacement_file>")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == 'read':
        filepath = sys.argv[2]
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        end = int(sys.argv[4]) if len(sys.argv) > 4 else None
        read_file(filepath, start, end)
    elif cmd == 'search':
        path = sys.argv[2]
        query = sys.argv[3]
        ext = sys.argv[4] if len(sys.argv) > 4 else None
        search_text(path, query, ext)
    elif cmd == 'replace':
        filepath = sys.argv[2]
        target_file = sys.argv[3]
        rep_file = sys.argv[4]
        replace_content(filepath, target_file, rep_file)
