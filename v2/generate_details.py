import os
import json
import re

def escape_html(val):
    if val is None:
        return ""
    return str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def clean_note(note):
    # Remove any trailing arrows or Unicode characters that were remnants from v1 formatting
    return re.sub(r'\s*(?:↗|\u00e2\u2020\u2014)[^\n]*$', '', str(note)).strip()

def format_status(status):
    if status == 'done':
        return '✓ Fulfilled'
    elif status == 'inprogress':
        return '◑ In Progress'
    elif status == 'evaded':
        return '✗ Evaded'
    return 'Pending'

def get_status_class(status):
    if status == 'done':
        return 'done'
    elif status == 'inprogress':
        return 'inprogress'
    elif status == 'evaded':
        return 'evaded'
    return 'pending'

def main():
    # Set paths relative to v2 directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    details_dir = os.path.join(base_dir, 'details')
    
    # Ensure details directory exists
    os.makedirs(details_dir, exist_ok=True)
    
    # Load meta and promises
    with open(os.path.join(data_dir, 'meta.json'), 'r', encoding='utf-8') as f:
        meta = json.load(f)
    with open(os.path.join(data_dir, 'promises.json'), 'r', encoding='utf-8') as f:
        promises = json.load(f)
        
    categories_map = {c['id']: c for c in meta['categories']}
    
    generated_count = 0
    
    for p in promises:
        pid = p['id']
        status = p['status']
        update_count = p.get('updateCount', 0)
        
        # Check if this promise meets the criteria for a dedicated detail page
        # Status resolved (done, evaded) or Update overflow (>5 updates)
        if status in ['done', 'evaded'] or update_count > 5:
            # Search for related files inside v2/files/<pid>
            files_path = os.path.join(base_dir, 'files', pid)
            doc_images = []
            if os.path.exists(files_path):
                image_exts = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
                doc_images = sorted([
                    f for f in os.listdir(files_path)
                    if os.path.isfile(os.path.join(files_path, f)) and f.lower().endswith(image_exts)
                ])

            # Load the specific update log if it exists
            update_file = os.path.join(data_dir, 'updates', f'{pid}.json')
            updates_data = {"updates": [], "counterEvidence": []}
            if os.path.exists(update_file):
                with open(update_file, 'r', encoding='utf-8') as uf:
                    updates_data = json.load(uf)
            
            category = categories_map.get(p['category'], {"title": p['category'], "icon": "📋"})
            
            # HTML Header & Title
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Promise Detail: {escape_html(p['highlight'] or p['text'][:40])} — BJP Sarkar Promise Tracker</title>
  
  <meta name="description" content="Detailed historical tracking, timeline, and supporting evidence for BJP Sarkar manifesto promise {escape_html(p['id'])}: {escape_html(p['text'][:140])}...">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Crimson+Pro:ital,wght@0,400;0,600;1,400;1,600&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../css/details.css">
</head>
<body>

  <!-- DETAIL MAIN CONTENT -->
  <div class="detail-container">
    <!-- TOP CLEAN NAVIGATION BAR -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 36px; border-bottom: 1px solid var(--rule-light); padding-bottom: 16px;">
      <a href="../index.html" class="detail-back-link" style="margin-bottom: 0; font-size: 11px; font-weight: 700;">
        ← Back to Tracker
      </a>
      <a href="../latest.html" class="detail-back-link" style="margin-bottom: 0; font-size: 11px; font-weight: 700; color: var(--saffron-dark);">
        Check Latest Updates →
      </a>
    </div>

    <!-- MAIN PROMISE CARD -->
    <div class="detail-card {get_status_class(status)}">
      <div class="detail-category-badge">
        <span>{escape_html(category['icon'])}</span>
        <span>{escape_html(category['title'])} • Promise #{escape_html(p['number'])}</span>
      </div>
      
      <h2 class="detail-promise-text">
        “{escape_html(p['text'])}”
      </h2>

      <div class="detail-meta-row">
        <div class="detail-meta-item">
          <span class="detail-meta-label">Status</span>
          <span class="detail-meta-value">
            <span class="note-tag note-{get_status_class(status)}" style="margin-top: 0;">{escape_html(format_status(status))}</span>
          </span>
        </div>
        <div class="detail-meta-item">
          <span class="detail-meta-label">Updates Logged</span>
          <span class="detail-meta-value">{escape_html(str(update_count))}</span>
        </div>
        <div class="detail-meta-item">
          <span class="detail-meta-label">Resolution Layer</span>
          <span class="detail-meta-value">{ "Done & Operational" if status == 'done' else ("Evaded / Rescinded" if status == 'evaded' else "In Progress") }</span>
        </div>
      </div>
    </div>

    <!-- TIMELINE OF UPDATES -->
    <div class="detail-timeline-section">
      <h3 class="detail-timeline-title">
        📋 Comprehensive Tracking History
      </h3>

      <div class="detail-timeline-wrap">
"""
            
            # Loop through individual updates
            updates_list = updates_data.get('updates', [])
            if not updates_list:
                html += f"""
        <div class="detail-timeline-card" style="text-align: center; color: var(--ink-faint); font-style: italic; padding: 40px;">
          No detailed update history available for this promise yet.
        </div>
"""
            else:
                for idx, u in enumerate(updates_list):
                    update_num = len(updates_list) - idx
                    sources = u.get('sources', [])
                    note_text = clean_note(u.get('note', ''))
                    date_label = ""
                    if sources:
                        date_label = re.split(r'[·|]', sources[0]['name'])[-1].strip()
                    
                    # Check if this update has nested counter-evidence
                    nested_counter_html = ""
                    nested_counters = u.get('counterEvidence', [])
                    if nested_counters:
                        for nc in nested_counters:
                            nc_sources = nc.get('sources', [])
                            nc_note = clean_note(nc.get('text', ''))
                            nc_sources_html = ""
                            if nc_sources:
                                nc_sources_html = f"""
                  <div class="detail-sources-list" style="margin-top: 8px;">
                    {"".join(f'<a href="{escape_html(s["url"])}" target="_blank" rel="noopener" class="detail-source-tag">{escape_html(s["name"])}</a>' for s in nc_sources)}
                  </div>
"""
                            nested_counter_html += f"""
                <div class="counter-block" style="margin-top: 16px; border-radius: 4px;">
                  <span class="counter-label">🛑 Counter Evidence: {escape_html(nc.get('label', 'Debatable'))}</span>
                  <div class="detail-timeline-note" style="font-size: 15px;">{escape_html(nc_note)}</div>
                  {nc_sources_html}
                </div>
"""
                    
                    sources_html = ""
                    if sources:
                        sources_html = f"""
            <div class="detail-evidence-box">
              <span class="detail-evidence-title">Official Sources & Media Coverage:</span>
              <div class="detail-sources-list">
                {"".join(f'<a href="{escape_html(s["url"])}" target="_blank" rel="noopener" class="detail-source-tag">{escape_html(s["name"])}</a>' for s in sources)}
              </div>
            </div>
"""
                    
                    html += f"""
        <!-- Update {update_num} -->
        <div class="detail-timeline-item {get_status_class(status) if idx == 0 else ''}">
          <div class="detail-timeline-dot"></div>
          <div class="detail-timeline-card">
            <div class="detail-timeline-header">
              <span class="detail-timeline-badge">Update {update_num}</span>
              {f'<span class="detail-timeline-date">{escape_html(date_label)}</span>' if date_label else ''}
            </div>
            <div class="detail-timeline-note">
              {escape_html(note_text)}
            </div>
            {nested_counter_html}
            {sources_html}
          </div>
        </div>
"""

            # Loop through global counter evidence
            global_counters = updates_data.get('counterEvidence', [])
            if global_counters:
                html += """
      </div>
      
      <h3 class="detail-timeline-title" style="margin-top: 48px;">
        🛑 Context & Conflicting Reports
      </h3>
      <div style="display: flex; flex-direction: column; gap: 20px;">
"""
                for gc in global_counters:
                    gc_sources = gc.get('sources', [])
                    gc_note = clean_note(gc.get('text', ''))
                    gc_sources_html = ""
                    if gc_sources:
                        gc_sources_html = f"""
            <div class="detail-evidence-box">
              <span class="detail-evidence-title">Supporting Reports & Evidence:</span>
              <div class="detail-sources-list">
                {"".join(f'<a href="{escape_html(s["url"])}" target="_blank" rel="noopener" class="detail-source-tag">{escape_html(s["name"])}</a>' for s in gc_sources)}
              </div>
            </div>
"""
                    html += f"""
        <div class="counter-block" style="border-radius: 6px; padding: 24px;">
          <span class="counter-label" style="font-size: 11px;">🛑 Counter Evidence: {escape_html(gc.get('label', 'Contradicted'))}</span>
          <div class="detail-timeline-note">{escape_html(gc_note)}</div>
          {gc_sources_html}
        </div>
"""

            # Closing Timeline & Page Containers
            html += f"""
      </div>
    </div>
"""

            # Build and append the Document Viewer HTML if doc_images exists
            document_viewer_html = ""
            if doc_images:
                # Compile javascript array of image links
                js_image_list = ", ".join(f'"../files/{escape_html(pid)}/{escape_html(f)}"' for f in doc_images)
                
                # Compile page buttons for pagination
                pagination_buttons_html = ""
                if len(doc_images) > 1:
                    buttons = []
                    for idx in range(len(doc_images)):
                        active_class = "active" if idx == 0 else ""
                        buttons.append(f'<button class="doc-page-btn {active_class}" onclick="switchDocPage({idx})">Page {idx + 1}</button>')
                    pagination_buttons_html = f"""
        <div class="doc-pagination-bar">
          {"".join(buttons)}
        </div>
"""
                
                document_viewer_html = f"""
    <!-- OFFICIAL DOCUMENTS SINGLE VIEWER BOX -->
    <div class="document-viewer-section">
      <h3 class="detail-timeline-title">
        📁 Official Notification & Gazette Documents
      </h3>
      <div class="doc-clean-card">
        <div style="width: 100%; overflow: hidden; display: flex; justify-content: center; align-items: flex-start; background: #fff; padding: 4px;">
          <img id="doc-active-image" src="../files/{escape_html(pid)}/{escape_html(doc_images[0])}" alt="Official Notification Page 1" class="doc-clean-image" style="transition: opacity 0.15s ease;">
        </div>
        {pagination_buttons_html}
      </div>
    </div>

    <script>
      const documentPages = [{js_image_list}];
      function switchDocPage(index) {{
        const img = document.getElementById('doc-active-image');
        if (!img) return;
        img.style.opacity = 0;
        setTimeout(() => {{
          img.src = documentPages[index];
          img.alt = "Official Notification Page " + (index + 1);
          img.style.opacity = 1;
        }}, 150);
        
        const btns = document.querySelectorAll('.doc-page-btn');
        btns.forEach((btn, idx) => {{
          if (idx === index) {{
            btn.classList.add('active');
          }} else {{
            btn.classList.remove('active');
          }}
        }});
      }}
    </script>
"""
            if document_viewer_html:
                html += document_viewer_html

            # Adding the accountability/future-proofing callout, NO footer, and closing tags
            html += f"""
    <!-- FUTURE-PROOFING & PUBLIC ACCOUNTABILITY BANNER -->
    <div class="detail-extensibility-note">
      <p class="detail-extensibility-text">
        <strong>⚖️ Public Accountability & Permanent Record:</strong> This page serves as a long-term historical record. Even after a promise is marked as "Fulfilled," we will continue to post updates here to track future changes, policy alterations, or ground-level execution success. If implementation fails in the future, it will be noted.
      </p>
    </div>
  </div>

</body>
</html>
"""
            
            # Write to HTML file
            out_file = os.path.join(details_dir, f'{pid}.html')
            with open(out_file, 'w', encoding='utf-8') as out_f:
                out_f.write(html)
            print(f"Generated detail page for promise: {pid}")
            generated_count += 1
            
    print(f"Detail pages generation complete. Total pages created/updated: {generated_count}")

if __name__ == '__main__':
    main()
