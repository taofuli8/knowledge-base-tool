import gradio as gr
import json
import httpx
from typing import List

API_BASE = "http://127.0.0.1:8000/api"


def get_stats():
    try:
        resp = httpx.get(f"{API_BASE}/stats")
        return resp.json()
    except Exception:
        return {"total": 0, "url": 0, "tutorial": 0, "github": 0, "pending": 0}


def get_tags():
    try:
        resp = httpx.get(f"{API_BASE}/tags")
        return resp.json()
    except Exception:
        return []


def list_entries(page=1, content_type=None):
    try:
        params = {"page": page, "page_size": 20}
        if content_type and content_type != "All":
            params["content_type"] = content_type.lower()
        resp = httpx.get(f"{API_BASE}/entries", params=params)
        return resp.json()
    except Exception as e:
        return {"total": 0, "page": 1, "page_size": 20, "items": [], "error": str(e)}


def search_entries(query, page=1, content_type=None, selected_tags=None):
    try:
        params = {"q": query, "page": page, "page_size": 20}
        if content_type and content_type != "All":
            params["content_type"] = content_type.lower()
        if selected_tags:
            params["tags"] = ",".join(selected_tags)
        resp = httpx.get(f"{API_BASE}/entries/search", params=params)
        return resp.json()
    except Exception as e:
        return {"total": 0, "page": 1, "page_size": 20, "items": [], "error": str(e)}


def create_entry(content_type, url, title, raw_content):
    try:
        data = {"content_type": content_type.lower(), "url": url or "", "title": title or "", "raw_content": raw_content or ""}
        resp = httpx.post(f"{API_BASE}/entries", json=data)
        if resp.status_code == 200:
            entry = resp.json()
            return f"Created entry #{entry['id']}: {entry['title']}", entry["id"]
        return f"Error: {resp.text}", None
    except Exception as e:
        return f"Error: {str(e)}", None


def get_entry(entry_id):
    try:
        resp = httpx.get(f"{API_BASE}/entries/{entry_id}")
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def update_entry_info(entry_id, title, summary, tags_str):
    try:
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        data = {"title": title, "summary": summary, "tags": tags}
        resp = httpx.put(f"{API_BASE}/entries/{entry_id}", json=data)
        if resp.status_code == 200:
            return "Updated successfully", resp.json()
        return f"Error: {resp.text}", None
    except Exception as e:
        return f"Error: {str(e)}", None


def delete_entry(entry_id):
    try:
        resp = httpx.delete(f"{API_BASE}/entries/{entry_id}")
        if resp.status_code == 200:
            return "Deleted successfully"
        return f"Error: {resp.text}"
    except Exception as e:
        return f"Error: {str(e)}"


def format_entry_card(entry):
    tags_html = "".join([f'<span style="background:#e0e7ff;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:4px">{t}</span>' for t in entry.get("tags", [])])
    type_icons = {"url": "🔗", "tutorial": "📝", "github": "🐙"}
    icon = type_icons.get(entry.get("content_type", ""), "📄")
    return f"""
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:12px;cursor:pointer" onclick="document.getElementById('detail_input').value={entry['id']};return false;">
    <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>{icon} {entry.get('title', 'Untitled')}</strong>
        <span style="color:#6b7280;font-size:12px">{entry.get('created_at', '')[:10]}</span>
    </div>
    <div style="color:#4b5563;font-size:14px;margin-top:8px">{entry.get('summary', 'No summary yet')[:200]}{'...' if len(entry.get('summary', '')) > 200 else ''}</div>
    <div style="margin-top:8px">{tags_html}</div>
</div>
"""


def format_entry_detail(entry):
    if not entry:
        return "Entry not found"
    tags = ", ".join(entry.get("tags", []))
    return f"""
## {entry.get('title', 'Untitled')}

**Type:** {entry.get('content_type')}
**URL:** {entry.get('url', 'N/A')}
**Status:** {entry.get('status')}
**Tags:** {tags}
**Created:** {entry.get('created_at')}
**Updated:** {entry.get('updated_at')}

---

### Summary
{entry.get('summary', 'No summary yet')}

---

### Raw Content
```
{entry.get('raw_content', '')[:2000]}{'...' if len(entry.get('raw_content', '')) > 2000 else ''}
```
"""


def build_stats_display(stats):
    return f"""
<div style="display:flex;gap:20px;flex-wrap:wrap">
    <div style="flex:1;min-width:120px;text-align:center;padding:16px;background:#f0f9ff;border-radius:8px">
        <div style="font-size:24px;font-weight:bold;color:#0369a1">{stats.get('total', 0)}</div>
        <div style="font-size:14px;color:#6b7280">Total</div>
    </div>
    <div style="flex:1;min-width:120px;text-align:center;padding:16px;background:#f0fdf4;border-radius:8px">
        <div style="font-size:24px;font-weight:bold;color:#15803d">{stats.get('url', 0)}</div>
        <div style="font-size:14px;color:#6b7280">URLs</div>
    </div>
    <div style="flex:1;min-width:120px;text-align:center;padding:16px;background:#fefce8;border-radius:8px">
        <div style="font-size:24px;font-weight:bold;color:#a16207">{stats.get('tutorial', 0)}</div>
        <div style="font-size:14px;color:#6b7280">Tutorials</div>
    </div>
    <div style="flex:1;min-width:120px;text-align:center;padding:16px;background:#faf5ff;border-radius:8px">
        <div style="font-size:24px;font-weight:bold;color:#7e22ce">{stats.get('github', 0)}</div>
        <div style="font-size:14px;color:#6b7280">GitHub</div>
    </div>
</div>
"""


def build_ui():
    with gr.Blocks(title="Knowledge Base") as app:
        gr.Markdown("# Knowledge Base Manager")

        with gr.Tabs():
            with gr.Tab("Overview"):
                stats_output = gr.HTML()
                recent_output = gr.HTML()
                refresh_btn = gr.Button("Refresh", variant="primary")

                def refresh_overview():
                    stats = get_stats()
                    entries = list_entries(1)
                    stats_html = build_stats_display(stats)
                    recent_html = "<h3>Recent Entries</h3>" + "".join([format_entry_card(e) for e in entries.get("items", [])])
                    return stats_html, recent_html

                refresh_btn.click(refresh_overview, outputs=[stats_output, recent_output])
                app.load(refresh_overview, outputs=[stats_output, recent_output])

            with gr.Tab("Search & Browse"):
                search_input = gr.Textbox(label="Search", placeholder="Enter keywords...")
                with gr.Row():
                    type_filter = gr.Dropdown(choices=["All", "URL", "Tutorial", "GitHub"], value="All", label="Type Filter")
                    tag_filter = gr.CheckboxGroup(label="Tag Filter", choices=[])

                def update_tag_choices():
                    tags = get_tags()
                    return gr.update(choices=[t["tag"] for t in tags])

                search_output = gr.HTML()
                page_num = gr.Number(value=1, label="Page", minimum=1)

                def do_search(query, ctype, selected_tags, page):
                    if not query:
                        return "Please enter search keywords"
                    results = search_entries(query, int(page), ctype, selected_tags)
                    if not results.get("items"):
                        return "No results found"
                    return "".join([format_entry_card(e) for e in results["items"]])

                search_btn = gr.Button("Search", variant="primary")
                search_btn.click(do_search, inputs=[search_input, type_filter, tag_filter, page_num], outputs=search_output)
                search_input.submit(do_search, inputs=[search_input, type_filter, tag_filter, page_num], outputs=search_output)
                type_filter.change(update_tag_choices, outputs=tag_filter)

            with gr.Tab("Create Entry"):
                with gr.Row():
                    with gr.Column():
                        create_type = gr.Dropdown(choices=["url", "tutorial", "github"], value="url", label="Content Type")
                        create_url = gr.Textbox(label="URL", placeholder="https://...")
                        create_title = gr.Textbox(label="Title", placeholder="Auto-filled for URL/GitHub types")
                        create_content = gr.Textbox(label="Content", placeholder="Paste tutorial content here (for tutorial type)", lines=10, visible=False)
                        create_btn = gr.Button("Create", variant="primary")

                create_msg = gr.Textbox(label="Result", interactive=False)

                def toggle_content_field(ctype):
                    return gr.update(visible=ctype == "tutorial")

                create_type.change(toggle_content_field, inputs=create_type, outputs=create_content)

                create_btn.click(create_entry, inputs=[create_type, create_url, create_title, create_content], outputs=[create_msg])

            with gr.Tab("Entry Detail"):
                detail_id = gr.Number(label="Entry ID", minimum=1, step=1)
                load_btn = gr.Button("Load", variant="primary")
                detail_display = gr.Markdown()
                detail_title = gr.Textbox(label="Title")
                detail_summary = gr.Textbox(label="Summary", lines=5)
                detail_tags = gr.Textbox(label="Tags (comma separated)")
                update_btn = gr.Button("Update", variant="primary")
                delete_btn = gr.Button("Delete", variant="stop")
                update_msg = gr.Textbox(label="Result", interactive=False)

                def load_detail(entry_id):
                    entry = get_entry(int(entry_id))
                    if not entry:
                        return format_entry_detail(None), "", "", ""
                    tags_str = ", ".join(entry.get("tags", []))
                    return format_entry_detail(entry), entry.get("title", ""), entry.get("summary", ""), tags_str

                load_btn.click(load_detail, inputs=detail_id, outputs=[detail_display, detail_title, detail_summary, detail_tags])

                update_btn.click(update_entry_info, inputs=[detail_id, detail_title, detail_summary, detail_tags], outputs=[update_msg, detail_display])
                delete_btn.click(delete_entry, inputs=detail_id, outputs=update_msg)

            with gr.Tab("Tags"):
                tags_output = gr.HTML()
                refresh_tags_btn = gr.Button("Refresh Tags", variant="primary")

                def display_tags():
                    tags = get_tags()
                    if not tags:
                        return "No tags yet"
                    html = "<div style='display:flex;flex-wrap:wrap;gap:8px'>"
                    for t in tags:
                        html += f'<span style="background:#e0e7ff;padding:6px 16px;border-radius:20px;font-size:14px">{t["tag"]} ({t["count"]})</span>'
                    html += "</div>"
                    return html

                refresh_tags_btn.click(display_tags, outputs=tags_output)
                app.load(display_tags, outputs=tags_output)

    return app


def create_app():
    return build_ui()
