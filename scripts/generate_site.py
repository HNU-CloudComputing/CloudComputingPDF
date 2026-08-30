import os
import re
import html

CCBOOK_PATH = "CCBook"
MAIN_TEX = os.path.join(CCBOOK_PATH, "main.tex")
TITLE_PATTERN = re.compile(r'\\(?:chapter|section)\*?\{([^}]+)\}')
BOOK_TITLE = "云计算原理与实践：以在线游戏为载体"
BOOK_FILE_STEM = BOOK_TITLE
LICENSE_URL = "https://github.com/HNU-CloudComputing/CloudComputingPDF/blob/main/LICENSE"
FULL_PDF_PATH = f"chapters/{BOOK_FILE_STEM}_全书.pdf"
MARKDOWN_URL = "https://hnu-cloudcomputing.github.io/CloudComputingMarkdown/"

def extract_chapters():
    with open(MAIN_TEX, "r", encoding="utf-8") as f:
        main_content = f.read()

    inputs = re.findall(r'\\input\{([^}]+)\}', main_content)
    chapters = []

    for item in inputs:
        item = item.strip()
        if "preamble" in item:
            continue

        tex_rel = item if item.endswith(".tex") else f"{item}.tex"
        tex_full = os.path.join(CCBOOK_PATH, tex_rel)

        if os.path.exists(tex_full):
            with open(tex_full, "r", encoding="utf-8") as tf:
                match = TITLE_PATTERN.search(tf.read())
                raw_title = match.group(1).strip() if match else os.path.splitext(os.path.basename(item))[0]
                # 清洗 LaTeX 指令与反斜杠
                clean_title = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', raw_title).replace('\\', ' ').strip()
                clean_title = re.sub(r'\s+', ' ', clean_title)
                
                key = os.path.splitext(os.path.basename(item))[0]
                chapters.append({
                    "key": key,
                    "rel_path": item if not item.endswith(".tex") else item[:-4],
                    "title": clean_title
                })
    return chapters

def generate_qmd(chapters):
    qmd = f"""---
title: "{BOOK_TITLE}"
page-layout: custom
toc: false
title-block-banner: false
---

<div class="course-page">
  <section class="course-hero" aria-labelledby="course-title">
    <div class="course-kicker">湖南大学 · 云计算课程教材</div>
    <div class="course-hero-grid">
      <div class="course-hero-copy">
        <h1 id="course-title">云计算原理与实践</h1>
        <p class="course-subtitle">以在线游戏为载体</p>
        <p class="course-lead">从在线系统的真实约束出发，系统讲解网络通信、单机并发、分布式协同与云原生部署。</p>
        <div class="course-actions">
          <a class="course-button course-button-primary" href="{FULL_PDF_PATH}">下载完整教材 PDF</a>
          <a class="course-button course-button-secondary" href="{MARKDOWN_URL}">阅读 Markdown 版</a>
        </div>
      </div>
      <dl class="course-meta">
        <div><dt>课程性质</dt><dd>本科专业选修课</dd></div>
        <div><dt>内容结构</dt><dd>前言 · 六章 · 两份附录</dd></div>
        <div><dt>阅读方式</dt><dd>完整 PDF 与分章 PDF</dd></div>
        <div><dt>编写单位</dt><dd>湖南大学 HNU GuoLab</dd></div>
      </dl>
    </div>
  </section>

  <section class="course-section" aria-labelledby="chapter-heading">
    <header class="course-section-heading">
      <span class="course-section-label">COURSE READER</span>
      <h2 id="chapter-heading">分章阅读</h2>
      <p>前言用于说明教材主线；第一至第六章按照课程进度组织，可直接在浏览器中打开对应 PDF。</p>
    </header>
    <div class="chapter-grid">
"""

    appendix_cards = []
    for ch in chapters:
        key = ch["key"]
        title = html.escape(ch["title"])
        key_lower = key.lower()
        if "appendix" in key_lower:
            appendix_cards.append(ch)
            continue
        if "intro" in key_lower:
            index_label = "导读"
            meta = "前言"
        else:
            num_match = re.search(r'\d+', key)
            index_label = f"{int(num_match.group(0)):02d}" if num_match else "章节"
            meta = "课程章节"
        qmd += f"""      <a class="chapter-card" href="chapters/chapter_{key}.pdf">
        <span class="chapter-index">{index_label}</span>
        <span class="chapter-copy"><strong>{title}</strong><small>{meta} · PDF</small></span>
        <span class="chapter-arrow" aria-hidden="true">→</span>
      </a>
"""

    qmd += """    </div>
  </section>
"""

    if appendix_cards:
        qmd += """  <section class="course-section course-section-compact" aria-labelledby="appendix-heading">
    <header class="course-section-heading">
      <span class="course-section-label">SUPPLEMENTARY MATERIAL</span>
      <h2 id="appendix-heading">附录</h2>
    </header>
    <div class="chapter-grid chapter-grid-appendix">
"""
        for ch in appendix_cards:
            key = ch["key"]
            title = html.escape(ch["title"])
            letter = key.replace("Appendix", "").replace("appendix", "") or "附录"
            qmd += f"""      <a class="chapter-card" href="chapters/chapter_{key}.pdf">
        <span class="chapter-index">{html.escape(letter)}</span>
        <span class="chapter-copy"><strong>{title}</strong><small>补充材料 · PDF</small></span>
        <span class="chapter-arrow" aria-hidden="true">→</span>
      </a>
"""
        qmd += """    </div>
  </section>
"""

    qmd += f"""  <section class="course-information" aria-label="教材与版权信息">
    <div>
      <span class="course-section-label">ABOUT THE BOOK</span>
      <h2>教材说明</h2>
      <p>教材以在线游戏为贯穿案例，但所讨论的规模、状态、故障和资源问题同样适用于在线协作、电商平台和大模型服务。</p>
    </div>
    <div>
      <span class="course-section-label">EDITORIAL TEAM</span>
      <h2>编写团队</h2>
      <p>核心编者与架构设计：陈果、徐方林、胡文举、庞海鑫、谢先衍、贺臻、张道平。</p>
      <p><a href="{LICENSE_URL}">版权与使用说明</a></p>
    </div>
  </section>
</div>
"""

    with open("index.qmd", "w", encoding="utf-8") as f:
        f.write(qmd)

def generate_compile_sh(chapters):
    sh_content = """#!/bin/bash
set -e
cd CCBook
echo "===> 1. 编译全书 main.tex..."
xelatex -interaction=nonstopmode main.tex || true
xelatex -interaction=nonstopmode main.tex || true

mkdir -p generated_chapters
"""
    for ch in chapters:
        sh_content += f"""
cat << 'TEX' > generated_chapters/gen_{ch['key']}.tex
\\input{{preamble.tex}}
\\begin{{document}}
\\input{{{ch['rel_path']}}}
\\end{{document}}
TEX
xelatex -interaction=nonstopmode generated_chapters/gen_{ch['key']}.tex || true
"""
    with open("run_latex.sh", "w", encoding="utf-8") as f:
        f.write(sh_content)
    os.chmod("run_latex.sh", 0o755)

if __name__ == "__main__":
    ch_list = extract_chapters()
    generate_qmd(ch_list)
    generate_compile_sh(ch_list)
    print("✅ index.qmd 与 run_latex.sh 均已成功动态生成")
