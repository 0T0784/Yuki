# ==========================================
# ticket_transcript.py
# チケット履歴をHTMLで保存
# ==========================================

from pathlib import Path


async def export_transcript(channel):
    messages = [m async for m in channel.history(limit=None)]

    html = "<html><body>"
    for m in reversed(messages):
        html += f"<p><b>{m.author}</b>: {m.content}</p>"
    html += "</body></html>"

    path = Path(f"transcripts/{channel.id}.html")
    path.parent.mkdir(exist_ok=True)
    path.write_text(html, encoding="utf-8")
