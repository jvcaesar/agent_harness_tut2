import sys, re
p = sys.argv[1]
lines = open(p, encoding="utf-8").read().splitlines()
void = {"meta", "link", "br", "img", "input", "hr"}
stack = []  # (tag, lineno)
bad = []
for i, raw in enumerate(lines, 1):
    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>", raw):
        o, tag, attrs, sl = m.groups()
        if tag.lower() in void:
            continue
        if o == "/":
            if not stack or stack[-1][0] != tag.lower():
                bad.append(("UNMATCHED </%s>" % tag, "line %d" % i, stack[-1] if stack else None, raw.strip()))
            else:
                stack.pop()
        else:
            if sl != "/":
                stack.append((tag.lower(), i))
print("unclosed:", [(t, l) for t, l in stack])
print("mismatch:", bad)