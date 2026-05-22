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

def split_into_sentences(text):
    sentences = []
    current_sentence = []
    abbrevs = {
        'no', 'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'vs', 'etc', 'eg', 'ie', 
        'rs', 'govt', 'dept', 'co', 'ltd', 'inc', 'corp', 'st', 'jan', 'feb', 'mar', 
        'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'approx', 'vol', 
        'pp', 'ed', 'gen', 'col', 'sen', 'rep', 'gov', 'ca', 'intl', 'sec', 'art', 
        'dir', 'dist', 'hq', 'dgp', 'sp', 'dm', 'sdm', 'bdo', 'sdo', 'wcd', 'wb', 
        'goa', 'hon', 'pb', 'hr', 'up', 'mp', 'ap', 'tel'
    }

    in_bold = False
    i = 0
    text_len = len(text)
    while i < text_len:
        if text.startswith('**', i):
            in_bold = not in_bold
            current_sentence.append('**')
            i += 2
            continue
        
        char = text[i]
        current_sentence.append(char)

        if not in_bold and char in ('.', '?', '!'):
            is_last = (i == text_len - 1)
            is_followed_by_space = not is_last and text[i + 1].isspace()

            if is_last or is_followed_by_space:
                is_sentence_end = True

                if char == '.':
                    j = i - 1
                    word_chars = []
                    while j >= 0 and (text[j].isalnum() or text[j] in ('.', '-')):
                        word_chars.append(text[j])
                        j -= 1
                    word = "".join(reversed(word_chars))
                    cleaned_word = re.sub(r'[^a-zA-Z0-9]', '', word).lower()
                    if cleaned_word in abbrevs:
                        is_sentence_end = False
                    if len(cleaned_word) == 1 and cleaned_word.isalpha():
                        is_sentence_end = False

                if is_sentence_end:
                    i += 1
                    # consume closing characters and whitespace
                    while i < text_len and (text[i] in ('"', "'", ')', ']', '}') or text[i].isspace()):
                        current_sentence.append(text[i])
                        i += 1
                    sentences.append("".join(current_sentence).strip())
                    current_sentence = []
                    continue
        i += 1

    if current_sentence:
        sentences.append("".join(current_sentence).strip())
    
    return [s for s in sentences if s]

def chunk_paragraphs(text, max_len=360):
    if not text:
        return []
    raw_paragraphs = re.split(r'\n\s*\n', str(text))
    final_paragraphs = []

    for raw_p in raw_paragraphs:
        trimmed = raw_p.strip()
        if not trimmed:
            continue

        if len(trimmed) <= max_len:
            final_paragraphs.append(trimmed)
            continue

        sentences = split_into_sentences(trimmed)
        current_group = []
        current_len = 0

        for sentence in sentences:
            if current_len > 0 and current_len + len(sentence) > max_len:
                final_paragraphs.append(" ".join(current_group))
                current_group = [sentence]
                current_len = len(sentence)
            else:
                current_group.append(sentence)
                current_len += (1 if current_len > 0 else 0) + len(sentence)
        if current_group:
            final_paragraphs.append(" ".join(current_group))
            
    return final_paragraphs

def format_note_text(text):
    if not text:
        return ""
    paras = chunk_paragraphs(str(text), 360)
    formatted = []
    for p in paras:
        if p.strip():
            escaped = escape_html(p.strip())
            # Convert Markdown **bold** to <strong>bold</strong>
            bolded = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
            formatted.append(f"<p>{bolded}</p>")
    return "".join(formatted)

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
        # Status resolved (done, evaded) or Update overflow (>=4 updates)
        if status in ['done', 'evaded'] or update_count >= 4:
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
  <title>Promise Detail: {escape_html(p['highlight'] or p['text'][:40])} — WB Accountability Tracker</title>
  
  <meta name="description" content="Detailed historical tracking, timeline, and supporting evidence for BJP Sarkar manifesto promise {escape_html(p['id'])}: {escape_html(p['text'][:140])}...">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Crimson+Pro:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Crimson+Pro:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" media="print" onload="this.media='all'">
  <noscript>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Crimson+Pro:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap">
  </noscript>
  <link rel="preload" href="../css/style.css" as="style">
  <link rel="preload" href="../css/details.css" as="style">
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../css/details.css">
</head>
<body>

  <!-- DETAIL MAIN CONTENT -->
  <div class="detail-container">
    <!-- TOP CLEAN NAVIGATION BAR -->
    <div class="detail-nav-bar">
      <a href="../index.html" class="detail-back-link">
        ← Back to Tracker
      </a>
      <a href="../latest.html" class="detail-back-link secondary">
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
          <span class="detail-meta-value">{escape_html(p.get('resolution') or ("Done & Operational" if status == 'done' else ("Evaded / Rescinded" if status == 'evaded' else "In Progress")))}</span>
        </div>
      </div>
      {f'''
      <div class="detail-resolution-note">
        ⚠️ <strong>Note on Resolution:</strong> {escape_html(p['resolutionNote'])}
      </div>
      ''' if p.get('resolutionNote') else ''}
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
                  <div class="detail-timeline-note" style="font-size: 16px;">{format_note_text(nc_note)}</div>
                  {nc_sources_html}
                </div>
"""
                    
                    # Check if this update has nested additional notes
                    nested_note_html = ""
                    nested_notes = u.get('additionalNotes', [])
                    if nested_notes:
                        for nn in nested_notes:
                            nn_sources = nn.get('sources', [])
                            nn_note = clean_note(nn.get('text', ''))
                            nn_sources_html = ""
                            if nn_sources:
                                nn_sources_html = f"""
                  <div class="detail-sources-list" style="margin-top: 8px;">
                    {"".join(f'<a href="{escape_html(s["url"])}" target="_blank" rel="noopener" class="detail-source-tag">{escape_html(s["name"])}</a>' for s in nn_sources)}
                  </div>
"""
                            nested_note_html += f"""
                <div class="note-block" style="margin-top: 16px; border-left: 3px solid var(--saffron-mid); padding-left: 12px; background: rgba(232, 98, 10, 0.02); border-radius: 0 4px 4px 0; padding-top: 8px; padding-bottom: 8px;">
                  <span class="note-label" style="font-family: var(--font-mono), monospace; font-size: 11px; font-weight: 700; color: var(--saffron-dark); text-transform: uppercase; display: flex; align-items: center; gap: 4px;">📌 Note: {escape_html(nn.get('label', 'Additional Note'))}</span>
                  <div class="detail-timeline-note" style="font-size: 16px; margin-top: 6px;">{format_note_text(nn_note)}</div>
                  {nn_sources_html}
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
              {format_note_text(note_text)}
            </div>
            {nested_counter_html}
            {nested_note_html}
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
          <div class="detail-timeline-note">{format_note_text(gc_note)}</div>
          {gc_sources_html}
        </div>
"""

            # Loop through global additional notes
            global_notes = updates_data.get('additionalNotes', [])
            if global_notes:
                # If we closed the updates list div, don't open it again unless we check if closed
                # Actually, the div closes when global_counters is present, but let's be extremely clean:
                if not global_counters:
                    html += """
      </div>
"""
                html += """
      <h3 class="detail-timeline-title" style="margin-top: 48px;">
        📌 Additional Context & Notes
      </h3>
      <div style="display: flex; flex-direction: column; gap: 20px;">
"""
                for gn in global_notes:
                    gn_sources = gn.get('sources', [])
                    gn_note = clean_note(gn.get('text', ''))
                    gn_sources_html = ""
                    if gn_sources:
                        gn_sources_html = f"""
            <div class="detail-evidence-box">
              <span class="detail-evidence-title">Supporting Sources:</span>
              <div class="detail-sources-list">
                {"".join(f'<a href="{escape_html(s["url"])}" target="_blank" rel="noopener" class="detail-source-tag">{escape_html(s["name"])}</a>' for s in gn_sources)}
              </div>
            </div>
"""
                    html += f"""
        <div class="note-block" style="border-radius: 6px; padding: 24px; border-left: 3px solid var(--saffron-mid); background: rgba(232, 98, 10, 0.02);">
          <span class="note-label" style="font-family: var(--font-mono), monospace; font-size: 11px; font-weight: 700; color: var(--saffron-dark); text-transform: uppercase;">📌 Note: {escape_html(gn.get('label', 'Additional Note'))}</span>
          <div class="detail-timeline-note" style="margin-top: 6px; font-size: 16px; line-height: 1.5; color: var(--ink-mid);">{format_note_text(gn_note)}</div>
          {gn_sources_html}
        </div>
"""

            # Closing Timeline & Page Containers
            # Make sure we close updates div if neither global_counters nor global_notes are present
            if not global_counters and not global_notes:
                html += """
      </div>
"""
            
            html += f"""
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
  <script src="../js/share.js" defer></script>

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
