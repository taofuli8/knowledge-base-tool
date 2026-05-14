import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .api import router
from . import crud

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = FastAPI(title="Knowledge Base API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup():
    init_db()


def esc(s):
    if not s:
        return ""
    return (s
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))


@app.get("/")
def root():
    stats = crud.get_entry_count()
    tags = crud.get_all_tags()
    total, items = crud.list_entries(1, 20)

    tags_show = tags[:20]
    tags_hidden = tags[20:]

    tags_html = "".join(
        f'<button class="tag-btn" onclick="toggleTag(this, \'{esc(t["tag"])}\')">{esc(t["tag"])} ({t["count"]})</button>'
        for t in tags_show
    )

    tags_hidden_html = ""
    if tags_hidden:
        tags_hidden_html = "".join(
            f'<button class="tag-btn" style="display:none" onclick="toggleTag(this, \'{esc(t["tag"])}\')">{esc(t["tag"])} ({t["count"]})</button>'
            for t in tags_hidden
        )

    toggle_attr = f' data-total="{len(tags)}"' if tags_hidden else ''

    type_icons = {"github": "GitHub", "url": "链接", "tutorial": "教程"}
    entries_html = ""
    if items:
        for e in items:
            tags_badge = "".join(f'<span class="entry-tag">{esc(t)}</span>' for t in (e.get("tags") or []))
            summary = e.get("summary") or "暂无简介"
            summary_display = esc(summary)[:200] + ("..." if len(summary) > 200 else "")
            date_str = (e.get("created_at") or "")[:10]
            type_label = type_icons.get(e.get("content_type", ""), e.get("content_type", ""))
            entries_html += f"""
            <div class="entry-card" onclick="showDetail({e['id']})">
                <div class="entry-header">
                    <div class="entry-title">
                        <span class="type-badge type-{e['content_type']}">{type_label}</span>
                        {esc(e['title'])}
                    </div>
                    <div class="entry-date">{date_str}</div>
                </div>
                <div class="entry-summary">{summary_display}</div>
                <div class="entry-tags">{tags_badge}</div>
                {f'<div class="entry-url">{esc(e["url"])}</div>' if e.get("url") else ""}
            </div>
            """
    else:
        entries_html = '<div class="loading">暂无条目</div>'

    pages = max(1, (total + 19) // 20)
    pagination_html = ""
    if pages > 1:
        pagination_html = f"""
        <button onclick="goPage(1)" {'disabled' if 1 <= 1 else ''}>首页</button>
        <button onclick="goPage(0)" disabled>上一页</button>
        <span>第 1 页 / 共 {pages} 页 ({total} 条)</span>
        <button onclick="goPage(2)" {'disabled' if 2 > pages else ''}>下一页</button>
        <button onclick="goPage({pages})">末页</button>
        """

    stats_json = json.dumps(stats)
    tags_json = json.dumps(tags)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Base</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 24px; margin-bottom: 12px; position: relative; padding-right: 80px; }}
        .stats {{ display: flex; gap: 16px; flex-wrap: wrap; }}
        .stat-card {{ background: #f8f9fa; padding: 16px 24px; border-radius: 8px; text-align: center; min-width: 120px; }}
        .stat-card .num {{ font-size: 28px; font-weight: bold; color: #1a73e8; }}
        .stat-card .label {{ font-size: 14px; color: #666; margin-top: 4px; }}
        .add-btn {{ position: absolute; top: 20px; right: 20px; background: #10b981; color: #fff; border: none; border-radius: 6px; padding: 8px 20px; font-size: 14px; cursor: pointer; font-weight: 600; }}
        .add-btn:hover {{ background: #059669; }}
        .search-bar {{ background: #fff; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
        .search-bar input[type="text"] {{ flex: 1; min-width: 200px; padding: 10px 16px; border: 1px solid #ddd; border-radius: 6px; font-size: 15px; outline: none; }}
        .search-bar input[type="text"]:focus {{ border-color: #1a73e8; }}
        .search-bar select {{ padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; background: #fff; }}
        .search-bar button {{ padding: 10px 24px; background: #1a73e8; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; }}
        .search-bar button:hover {{ background: #1557b0; }}
        .tags-bar {{ background: #fff; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; flex-direction: column; gap: 8px; }}
        .tags-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .tags-header span {{ font-size: 14px; color: #666; font-weight: 500; }}
        .tags-toggle {{ font-size: 13px; color: #1a73e8; background: none; border: none; cursor: pointer; padding: 4px 8px; border-radius: 4px; }}
        .tags-toggle:hover {{ background: #f0f0f0; }}
        .tags-wrap {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .tag-btn {{ padding: 4px 12px; background: #e8f0fe; color: #1a73e8; border: none; border-radius: 16px; cursor: pointer; font-size: 13px; white-space: nowrap; }}
        .tag-btn.active {{ background: #1a73e8; color: #fff; }}
        .entry-list {{ display: flex; flex-direction: column; gap: 12px; }}
        .entry-card {{ background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); cursor: pointer; transition: box-shadow 0.2s; }}
        .entry-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .entry-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }}
        .entry-title {{ font-size: 18px; font-weight: 600; color: #1a73e8; display: flex; align-items: center; gap: 8px; }}
        .entry-date {{ font-size: 13px; color: #999; white-space: nowrap; }}
        .entry-summary {{ font-size: 14px; color: #555; line-height: 1.6; margin-bottom: 10px; }}
        .entry-tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
        .entry-tag {{ padding: 2px 10px; background: #f0f0f0; border-radius: 12px; font-size: 12px; color: #666; }}
        .entry-url {{ font-size: 12px; color: #999; margin-top: 8px; word-break: break-all; }}
        .type-badge {{ padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }}
        .type-github {{ background: #f0f0f0; color: #333; }}
        .type-url {{ background: #e8f5e9; color: #2e7d32; }}
        .type-tutorial {{ background: #fff3e0; color: #ef6c00; }}
        .detail-modal {{ display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; overflow-y: auto; }}
        .detail-modal.show {{ display: flex; justify-content: center; align-items: flex-start; padding: 40px 20px; }}
        .detail-content {{ background: #fff; border-radius: 12px; max-width: 800px; width: 100%; padding: 32px; position: relative; }}
        .detail-close {{ position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 24px; cursor: pointer; color: #666; }}
        .detail-title {{ font-size: 22px; font-weight: 600; margin-bottom: 16px; color: #1a73e8; }}
        .detail-meta {{ display: flex; gap: 16px; margin-bottom: 16px; font-size: 14px; color: #666; flex-wrap: wrap; }}
        .detail-summary {{ font-size: 15px; line-height: 1.8; color: #333; margin-bottom: 20px; padding: 16px; background: #f8f9fa; border-radius: 8px; }}
        .detail-tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
        .detail-tag {{ padding: 4px 14px; background: #e8f0fe; color: #1a73e8; border-radius: 16px; font-size: 13px; }}
        .detail-actions {{ display: flex; gap: 12px; margin-bottom: 20px; }}
        .detail-actions button {{ padding: 8px 20px; border-radius: 6px; border: 1px solid #ddd; background: #fff; cursor: pointer; font-size: 14px; }}
        .detail-actions button.del {{ color: #d32f2f; border-color: #ffcdd2; }}
        .detail-actions button.edit-btn {{ color: #1a73e8; border-color: #bbdefb; }}
        .detail-raw {{ font-size: 13px; color: #888; line-height: 1.6; max-height: 300px; overflow-y: auto; white-space: pre-wrap; background: #fafafa; padding: 16px; border-radius: 8px; border: 1px solid #eee; }}
        .pagination {{ display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 20px; }}
        .pagination button {{ padding: 8px 16px; border: 1px solid #ddd; background: #fff; border-radius: 6px; cursor: pointer; }}
        .pagination button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .pagination span {{ font-size: 14px; color: #666; }}
        .loading {{ text-align: center; padding: 40px; color: #999; }}
        .edit-form {{ display: none; background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .edit-form.show {{ display: block; }}
        .edit-form input, .edit-form textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 12px; font-size: 14px; }}
        .edit-form textarea {{ min-height: 100px; resize: vertical; }}
        .edit-form .btn-row {{ display: flex; gap: 12px; }}
        .edit-form .btn-row button {{ padding: 8px 20px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; }}
        .edit-form .btn-row button.save {{ background: #1a73e8; color: #fff; }}
        .edit-form .btn-row button.cancel {{ background: #fff; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>知识库</h1>
            <div class="stats">
                <div class="stat-card"><div class="num">{stats['total']}</div><div class="label">总计</div></div>
                <div class="stat-card"><div class="num">{stats['github']}</div><div class="label">GitHub</div></div>
                <div class="stat-card"><div class="num">{stats['url']}</div><div class="label">链接</div></div>
                <div class="stat-card"><div class="num">{stats['tutorial']}</div><div class="label">教程</div></div>
            </div>
            <button class="add-btn" onclick="showAdd()">新增</button>
        </div>
        <div class="search-bar">
            <form onsubmit="return doSearch(event)">
                <input type="text" id="searchInput" placeholder="搜索关键词...">
            </form>
            <select id="typeFilter">
                <option value="">全部类型</option>
                <option value="github">GitHub</option>
                <option value="url">链接</option>
                <option value="tutorial">教程</option>
            </select>
            <button onclick="doSearch()">搜索</button>
            <button onclick="loadPage(1)" style="background:#666">浏览</button>
        </div>
        <div class="tags-bar" id="tagsBar">
            <div class="tags-header">
                <span>标签 ({len(tags)})：</span>
                {f'<button class="tags-toggle" id="tagsToggle" onclick="toggleTags()">展开</button>' if tags_hidden else ''}
            </div>
            <div class="tags-wrap" id="tagsWrap">
                {tags_html}{tags_hidden_html}
            </div>
        </div>
        <div class="entry-list" id="entryList">
            {entries_html}
        </div>
        <div class="pagination" id="pagination">
            {pagination_html}
        </div>
    </div>

    <div class="detail-modal" id="addModal">
        <div class="detail-content">
            <button class="detail-close" onclick="closeAdd()">&times;</button>
            <div class="detail-title">新增条目</div>
            <div class="edit-form" style="display:block;margin-top:16px">
                <label class="form-label" style="display:block;margin-bottom:4px;color:#666;font-size:13px">标题</label>
                <input type="text" id="addTitle" style="margin-bottom:12px">
                <label class="form-label" style="display:block;margin-bottom:4px;color:#666;font-size:13px">URL</label>
                <input type="text" id="addUrl" style="margin-bottom:12px">
                <label class="form-label" style="display:block;margin-bottom:4px;color:#666;font-size:13px">类型</label>
                <select id="addType" style="margin-bottom:12px">
                    <option value="github">GitHub</option>
                    <option value="url">链接</option>
                    <option value="tutorial">教程</option>
                </select>
                <label class="form-label" style="display:block;margin-bottom:4px;color:#666;font-size:13px">简介</label>
                <textarea id="addSummary" rows="3" style="margin-bottom:12px"></textarea>
                <label class="form-label" style="display:block;margin-bottom:4px;color:#666;font-size:13px">标签（用逗号分隔）</label>
                <input type="text" id="addTags" style="margin-bottom:16px">
                <div class="btn-row">
                    <button class="save" onclick="addEntry()">保存</button>
                    <button class="cancel" onclick="closeAdd()">取消</button>
                </div>
            </div>
        </div>
    </div>

    <div class="detail-modal" id="detailModal">
        <div class="detail-content">
            <button class="detail-close" onclick="closeDetail()">&times;</button>
            <div class="detail-title" id="detailTitle"></div>
            <div class="detail-meta" id="detailMeta"></div>
            <div class="detail-summary" id="detailSummary"></div>
            <div class="detail-tags" id="detailTags"></div>
            <div class="detail-actions">
                <button class="edit-btn" onclick="toggleEdit()">编辑</button>
                <button class="del" onclick="deleteEntry()">删除</button>
                <button id="openLinkBtn" onclick="">打开链接</button>
            </div>
            <div class="edit-form" id="editForm">
                <input type="text" id="editTitle" placeholder="标题">
                <textarea id="editSummary" placeholder="简介"></textarea>
                <input type="text" id="editTags" placeholder="标签（用逗号分隔）">
                <div class="btn-row">
                    <button class="save" onclick="saveEdit()">保存</button>
                    <button class="cancel" onclick="toggleEdit()">取消</button>
                </div>
            </div>
            <h4 style="margin-bottom:8px;color:#666">原始内容</h4>
            <div class="detail-raw" id="detailRaw"></div>
            <input type="hidden" id="detailUrl">
            <input type="hidden" id="detailId">
        </div>
    </div>

    <script>
        var STATS_DATA = {stats_json};
        var TAGS_DATA = {tags_json};
        var API = '/api';
        var activeTags = [];
        var tagsExpanded = false;

        function toggleTags() {{
            tagsExpanded = !tagsExpanded;
            var btns = document.querySelectorAll('#tagsWrap .tag-btn');
            for (var i = 20; i < btns.length; i++) {{
                btns[i].style.display = tagsExpanded ? '' : 'none';
            }}
            document.getElementById('tagsToggle').textContent = tagsExpanded ? '收起' : '展开';
        }}

        function esc(s) {{
            if (!s) return '';
            var d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }}

        function toggleTag(btn, tag) {{
            var idx = activeTags.indexOf(tag);
            if (idx >= 0) {{ activeTags.splice(idx, 1); btn.classList.remove('active'); }}
            else {{ activeTags.push(tag); btn.classList.add('active'); }}
            doSearch();
        }}

        function doSearch(e) {{
            if (e) e.preventDefault();
            var q = document.getElementById('searchInput').value.trim();
            var typeF = document.getElementById('typeFilter').value;
            if (!q && !typeF && activeTags.length === 0) {{ loadPage(1); return; }}
            var url = API + '/entries/search?page=1&page_size=20';
            if (q) url += '&q=' + encodeURIComponent(q);
            if (typeF) url += '&content_type=' + typeF;
            if (activeTags.length) url += '&tags=' + activeTags.join(',');
            var xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    var d = JSON.parse(xhr.responseText);
                    renderEntries(d.items);
                    renderPagination(d.total, 1, d.page_size);
                }}
            }};
            xhr.send();
        }}

        function loadPage(page) {{
            var typeF = document.getElementById('typeFilter').value;
            var url = API + '/entries?page=' + page + '&page_size=20';
            if (typeF) url += '&content_type=' + typeF;
            var xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    var d = JSON.parse(xhr.responseText);
                    renderEntries(d.items);
                    renderPagination(d.total, d.page, d.page_size);
                }}
            }};
            xhr.send();
        }}

        function renderEntries(items) {{
            var el = document.getElementById('entryList');
            if (!items.length) {{ el.innerHTML = '<div class="loading">暂无条目</div>'; return; }}
            var icons = {{ github: 'GitHub', url: '链接', tutorial: '教程' }};
            var html = '';
            for (var i = 0; i < items.length; i++) {{
                var e = items[i];
                var tags = '';
                if (e.tags) {{
                    for (var j = 0; j < e.tags.length; j++) tags += '<span class="entry-tag">' + esc(e.tags[j]) + '</span>';
                }}
                var summary = e.summary || '暂无简介';
                var sdisp = esc(summary).substring(0, 200);
                if (summary.length > 200) sdisp += '...';
                html += '<div class="entry-card" onclick="showDetail(' + e.id + ')">' +
                    '<div class="entry-header">' +
                    '<div class="entry-title"><span class="type-badge type-' + e.content_type + '">' + (icons[e.content_type] || e.content_type) + '</span>' + esc(e.title) + '</div>' +
                    '<div class="entry-date">' + ((e.created_at || '').substring(0, 10)) + '</div></div>' +
                    '<div class="entry-summary">' + sdisp + '</div>' +
                    '<div class="entry-tags">' + tags + '</div>' +
                    (e.url ? '<div class="entry-url">' + esc(e.url) + '</div>' : '') +
                    '</div>';
            }}
            el.innerHTML = html;
        }}

        function renderPagination(total, page, size) {{
            var pages = Math.ceil(total / size);
            var el = document.getElementById('pagination');
            if (pages <= 1) {{ el.innerHTML = ''; return; }}
            el.innerHTML = '<button onclick="loadPage(' + (page-1) + ')" ' + (page<=1?'disabled':'') + '>上一页</button>' +
                '<span>第 ' + page + ' 页 / 共 ' + pages + ' 页 (' + total + ' 条)</span>' +
                '<button onclick="loadPage(' + (page+1) + ')" ' + (page>=pages?'disabled':'') + '>下一页</button>';
        }}

        function showDetail(id) {{
            var xhr = new XMLHttpRequest();
            xhr.open('GET', API + '/entries/' + id, true);
            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    var e = JSON.parse(xhr.responseText);
                    document.getElementById('detailId').value = e.id;
                    document.getElementById('detailUrl').value = e.url || '';
                    document.getElementById('detailTitle').textContent = e.title;
                    document.getElementById('detailSummary').textContent = e.summary || '暂无简介';
                    var raw = e.raw_content || '';
                    document.getElementById('detailRaw').textContent = raw.substring(0, 3000) + (raw.length > 3000 ? '\\n...\\n[截断]' : '');
                    var typeNames = {{ github: 'GitHub', url: '链接', tutorial: '教程' }};
                    var statusNames = {{ pending: '待处理', completed: '已完成', failed: '失败' }};
                    document.getElementById('detailMeta').innerHTML = '<span>类型: ' + (typeNames[e.content_type] || e.content_type) + '</span><span>状态: ' + (statusNames[e.status] || e.status) + '</span><span>创建时间: ' + ((e.created_at||'').substring(0,10)) + '</span>';
                    var tagsHtml = '';
                    if (e.tags) {{ for (var j = 0; j < e.tags.length; j++) tagsHtml += '<span class="detail-tag">' + esc(e.tags[j]) + '</span>'; }}
                    document.getElementById('detailTags').innerHTML = tagsHtml;
                    document.getElementById('editTitle').value = e.title;
                    document.getElementById('editSummary').value = e.summary || '';
                    document.getElementById('editTags').value = (e.tags || []).join(', ');
                    var openBtn = document.getElementById('openLinkBtn');
                    if (e.url) {{ openBtn.style.display = ''; openBtn.onclick = function() {{ window.open(e.url, '_blank'); }}; }}
                    else {{ openBtn.style.display = 'none'; }}
                    document.getElementById('editForm').classList.remove('show');
                    document.getElementById('detailModal').classList.add('show');
                }}
            }};
            xhr.send();
        }}

        function closeDetail() {{ document.getElementById('detailModal').classList.remove('show'); }}
        function showAdd() {{ document.getElementById('addModal').classList.add('show'); }}
        function closeAdd() {{ document.getElementById('addModal').classList.remove('show'); }}

        function addEntry() {{
            var title = document.getElementById('addTitle').value.trim();
            var url = document.getElementById('addUrl').value.trim();
            var ctype = document.getElementById('addType').value;
            var summary = document.getElementById('addSummary').value.trim();
            var tags = document.getElementById('addTags').value.split(',').map(function(t) {{ return t.trim(); }}).filter(Boolean);
            if (!title) {{ alert('请输入标题'); return; }}
            var xhr = new XMLHttpRequest();
            xhr.open('POST', API + '/entries', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onload = function() {{
                if (xhr.status === 200 || xhr.status === 201) {{
                    closeAdd();
                    document.getElementById('addTitle').value = '';
                    document.getElementById('addUrl').value = '';
                    document.getElementById('addSummary').value = '';
                    document.getElementById('addTags').value = '';
                    loadPage(1);
                }} else {{
                    alert('添加失败: ' + xhr.responseText);
                }}
            }};
            xhr.send(JSON.stringify({{ title: title, url: url || null, content_type: ctype, summary: summary || null, tags: tags }}));
        }}

        function toggleEdit() {{ document.getElementById('editForm').classList.toggle('show'); }}

        function saveEdit() {{
            var id = document.getElementById('detailId').value;
            var tags = document.getElementById('editTags').value.split(',').map(function(t) {{ return t.trim(); }}).filter(Boolean);
            var xhr = new XMLHttpRequest();
            xhr.open('PUT', API + '/entries/' + id, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onload = function() {{
                if (xhr.status === 200) {{ showDetail(id); loadPage(1); }}
            }};
            xhr.send(JSON.stringify({{ title: document.getElementById('editTitle').value, summary: document.getElementById('editSummary').value, tags: tags }}));
        }}

        function deleteEntry() {{
            if (!confirm('确认删除该条目？')) return;
            var id = document.getElementById('detailId').value;
            var xhr = new XMLHttpRequest();
            xhr.open('DELETE', API + '/entries/' + id, true);
            xhr.onload = function() {{
                closeDetail(); loadPage(1);
            }};
            xhr.send();
        }}

        document.getElementById('searchInput').addEventListener('keydown', function(e) {{ if (e.key === 'Enter') doSearch(e); }});
    </script>
</body>
</html>"""

    return HTMLResponse(content=html)
