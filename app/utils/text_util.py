import re

FORBIDDEN_PATTERNS = [
    r"(give me|score me|grade me|award me).*?\d+\s*(point|points|score|grade)",
    r"(max|maximum|full).*?(point|points|score|grade)",
    r"(my (submission|work|answer)).*?(max|maximum|\d+\s*(point|points|score|grade))",
    r"(set|make).*?(point|points|score|grade).*?\d+",
    r"deserve.*?\d+\s*(point|points|score|grade)",
    r"(need|want|require).*?\d+\s*(point|points|score|grade)",
    r"(assign|allocate).*?\d+\s*(point|points|score|grade)",
    r"(credit|crediting).*?\d+\s*(point|points|score|grade)",
    r"(earn|earning).*?\d+\s*(point|points|score|grade)",
    r"(should (get|receive|have)).*?\d+\s*(point|points|score|grade)",
    r"(must (get|receive|have)).*?\d+\s*(point|points|score|grade)",
    r"\d+\s*(point|points|score|grade).*(please|pls)",
    r"(perfect|100%).*?(score|grade|point|points)",
    r"(bonus|extra).*?(point|points|score|grade)"
]


def check_content_submission(content: str) -> str:
    lines = content.split('\n')
    cleaned_content = []

    for line in lines:
        if not line.strip():
            cleaned_content.append(line)
            continue

        parts = re.split(r'([.!?;])', line)
        cleaned_parts = []

        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and parts[i + 1] in '.!?;':
                sentence = parts[i] + parts[i + 1]
                is_forbidden = any(re.search(pattern, parts[i].strip(), re.IGNORECASE)
                                   for pattern in FORBIDDEN_PATTERNS)

                if not is_forbidden and parts[i].strip():
                    cleaned_parts.append(sentence)
                elif not parts[i].strip():
                    cleaned_parts.append(parts[i + 1])

                i += 2
            else:
                if parts[i].strip():
                    is_forbidden = any(re.search(pattern, parts[i].strip(), re.IGNORECASE)
                                       for pattern in FORBIDDEN_PATTERNS)
                    if not is_forbidden:
                        cleaned_parts.append(parts[i])
                else:
                    cleaned_parts.append(parts[i])
                i += 1

        cleaned_line = ''.join(cleaned_parts)
        cleaned_content.append(cleaned_line)

    return '\n'.join(cleaned_content)
