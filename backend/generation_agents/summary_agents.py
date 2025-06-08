from typing import Optional

def get_summary_display_html(summary_text: str = "", title: str = "XRPL Loan Summary", metadata: Optional[dict] = None):
    """
    Generate HTML to display a summary string beautifully with markdown support
    
    Args:
        summary_text: The summary text to display (supports markdown)
        title: Title for the page
        metadata: Optional metadata to display (provider, timestamp, etc.)
    
    Returns:
        HTML string for displaying the summary
    """
    
    if not summary_text:
        summary_text = "No summary provided. Please generate a summary first."
    
    # Format metadata if provided, but exclude user_query since it's provider-generated
    metadata_html = ""
    if metadata:
        metadata_items = []
        for key, value in metadata.items():
            # Skip user_query as it's internal/provider-generated
            if key == "user_query":
                continue
            formatted_key = key.replace('_', ' ').title()
            metadata_items.append(f"<strong>{formatted_key}:</strong> {value}")
        
        if metadata_items:  # Only show metadata section if there are items to display
            metadata_html = f"""
            <div class="metadata">
                {' | '.join(metadata_items)}
            </div>
            """
    
    # Convert summary text to HTML-safe and handle basic markdown
    import html
    import re
    
    # Escape HTML but preserve our markdown processing
    safe_summary = html.escape(summary_text)
    
    # Process basic markdown elements
    # Headers (## Header)
    safe_summary = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', safe_summary, flags=re.MULTILINE)
    safe_summary = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', safe_summary, flags=re.MULTILINE)
    
    # Bold (**text** or __text__)
    safe_summary = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', safe_summary)
    safe_summary = re.sub(r'__(.*?)__', r'<strong>\1</strong>', safe_summary)
    
    # Italic (*text* or _text_)
    safe_summary = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', safe_summary)
    safe_summary = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<em>\1</em>', safe_summary)
    
    # Code blocks (```code```)
    safe_summary = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', safe_summary, flags=re.DOTALL)
    
    # Inline code (`code`)
    safe_summary = re.sub(r'`([^`]+?)`', r'<code>\1</code>', safe_summary)
    
    # Lists (- item or * item)
    lines = safe_summary.split('\n')
    processed_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if re.match(r'^[-*]\s+', stripped):
            if not in_list:
                processed_lines.append('<ul>')
                in_list = True
            item_text = re.sub(r'^[-*]\s+', '', stripped)
            processed_lines.append(f'<li>{item_text}</li>')
        else:
            if in_list:
                processed_lines.append('</ul>')
                in_list = False
            processed_lines.append(line)
    
    if in_list:
        processed_lines.append('</ul>')
    
    safe_summary = '\n'.join(processed_lines)
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary-area {{
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 30px;
            font-family: 'Georgia', serif;
            font-size: 16px;
            line-height: 1.8;
            white-space: pre-wrap;
            overflow-y: auto;
            max-height: 70vh;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        /* Markdown styling */
        .summary-area h2 {{
            color: #2a5298;
            font-size: 1.5em;
            margin: 20px 0 10px 0;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 5px;
        }}
        
        .summary-area h3 {{
            color: #667eea;
            font-size: 1.2em;
            margin: 15px 0 8px 0;
        }}
        
        .summary-area strong {{
            color: #2a5298;
            font-weight: 600;
        }}
        
        .summary-area em {{
            color: #6c757d;
            font-style: italic;
        }}
        
        .summary-area code {{
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #2a5298;
        }}
        
        .summary-area pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
        }}
        
        .summary-area ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        
        .summary-area li {{
            margin: 5px 0;
            color: #495057;
        }}
        
        .metadata {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 14px;
            color: #6c757d;
            text-align: center;
        }}
        
        .navigation {{
            background: rgba(102, 126, 234, 0.1);
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e9ecef;
        }}
        
        .nav-link {{
            color: #667eea;
            text-decoration: none;
            margin: 0 15px;
            font-weight: 500;
            transition: color 0.3s ease;
        }}
        
        .nav-link:hover {{
            color: #2a5298;
            text-decoration: underline;
        }}
        
        .empty-state {{
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 60px 20px;
        }}
        
        .empty-state-icon {{
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <p>AI-Powered Loan Analysis Results</p>
        </div>
        
        <div class="content">
            <div class="summary-area">
                {safe_summary if safe_summary.strip() else '<div class="empty-state"><div class="empty-state-icon">📝</div><p>No summary content available.<br>Please generate a summary first.</p></div>'}
            </div>
            
            {metadata_html}
        </div>
        
        <div class="navigation">
            <a href="/" class="nav-link">🏠 Home</a>
            <a href="/workflow/display" class="nav-link">🔄 Workflow</a>
            <a href="javascript:history.back()" class="nav-link">← Back</a>
            <a href="javascript:window.print()" class="nav-link">🖨️ Print</a>
        </div>
    </div>
</body>
</html>
"""

def get_summary_input_form_html():
    """Generate a simple form to input summary text for testing"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Summary Input Form</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .form-content {
            padding: 40px;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }
        
        textarea, input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        
        textarea:focus, input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea {
            height: 300px;
            resize: vertical;
            font-family: 'Courier New', monospace;
        }
        
        .submit-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
            width: 100%;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        
        .markdown-help {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 12px;
            color: #6c757d;
        }
        
        .markdown-help h4 {
            margin-bottom: 8px;
            color: #495057;
        }
        
        .markdown-example {
            font-family: monospace;
            background: #e9ecef;
            padding: 2px 4px;
            border-radius: 3px;
            margin: 0 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Summary Input</h1>
            <p>Enter summary text to display (Markdown supported)</p>
        </div>
        
        <div class="form-content">
            <div class="markdown-help">
                <h4>📚 Markdown Support:</h4>
                <p>
                    <span class="markdown-example">**bold**</span> → <strong>bold</strong> | 
                    <span class="markdown-example">*italic*</span> → <em>italic</em> | 
                    <span class="markdown-example">## Heading</span> → Header | 
                    <span class="markdown-example">- List item</span> → Bullet point | 
                    <span class="markdown-example">`code`</span> → inline code
                </p>
            </div>
            
            <form action="/api/display-summary" method="post">
                <div class="form-group">
                    <label for="title">Summary Title:</label>
                    <input type="text" id="title" name="title" value="XRPL Loan Analysis Summary" placeholder="Enter title for the summary">
                </div>
                
                <div class="form-group">
                    <label for="summary_text">Summary Content (Markdown supported):</label>
                    <textarea id="summary_text" name="summary_text" placeholder="Enter your summary text here...

Example with Markdown:
## 🏦 XRPL MICROLOAN ANALYSIS

### 👤 USER PROFILE:
- **Name:** John Doe
- **Amount:** 2.5 XRP
- **Status:** Approved

### 📊 RISK ASSESSMENT:
- **Risk Level:** Low
- **Score:** 3/10
   
### 💰 RECOMMENDATIONS:
- Proceed with loan approval
- Monitor repayment schedule
- Consider rate adjustment

**Note:** This supports markdown formatting!"></textarea>
                </div>
                
                <button type="submit" class="submit-btn">
                    📊 Display Summary
                </button>
            </form>
        </div>
    </div>
</body>
</html>
"""
