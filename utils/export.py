from datetime import datetime


def to_markdown(messages: list[dict]) -> str:
    lines = [
        f"# Chat Export — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"### {role}")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)
