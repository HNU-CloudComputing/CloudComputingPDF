import argparse
import os
import re
import html
import json
import subprocess

TITLE_PATTERN = re.compile(r'\\(?:chapter|section)\*?\{([^}]+)\}')
BOOK_TITLE = "云计算原理与实践：以在线游戏为载体"
BOOK_FILE_STEM = BOOK_TITLE
LICENSE_URL = "https://github.com/HNU-CloudComputing/CloudComputingPDF/blob/main/LICENSE"
FULL_PDF_PATH = f"chapters/{BOOK_FILE_STEM}_全书.pdf"
MARKDOWN_URL = "https://hnu-cloudcomputing.github.io/CloudComputingMarkdown/"

def extract_chapters(ccbook_path="CCBook"):
    main_tex = os.path.join(ccbook_path, "main.tex")
    with open(main_tex, "r", encoding="utf-8") as f:
        main_content = f.read()

    inputs = re.findall(r'\\input\{([^}]+)\}', main_content)
    chapters = []

    for item in inputs:
        item = item.strip()
        if "preamble" in item:
            continue

        tex_rel = item if item.endswith(".tex") else f"{item}.tex"
        tex_full = os.path.join(ccbook_path, tex_rel)

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

def get_source_metadata(ccbook_path):
    def git_value(format_string, fallback):
        try:
            result = subprocess.run(
                ["git", "-C", ccbook_path, "log", "-1", f"--format={format_string}"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() or fallback
        except (OSError, subprocess.CalledProcessError):
            return fallback

    return {
        "date": git_value("%cs", "持续更新"),
    }


def generate_qmd(chapters, source_metadata, output_path="index.qmd"):
    edition_date = html.escape(source_metadata["date"])
    qmd = f"""---
title: "{BOOK_TITLE}"
page-layout: custom
toc: false
title-block-banner: false
---

```{{=html}}
<div class="publication-page">
  <div class="edition-ribbon" aria-label="版本信息">
    <span>HUNAN UNIVERSITY · DIGITAL TEXTBOOK</span>
    <span>PDF EDITION / {edition_date}</span>
  </div>

  <section class="publication-hero" aria-labelledby="publication-title">
    <div class="book-object" aria-hidden="true">
      <div class="book-spine">HNU · CLOUD COMPUTING</div>
      <div class="book-cover">
        <span class="book-cover-series">湖南大学计算机学院 · 云计算课程教材</span>
        <div class="book-cover-title">云计算<br>原理与实践</div>
        <span class="book-cover-subtitle">以在线游戏为载体</span>
        <span class="book-cover-imprint">GUOLAB · PDF EDITION</span>
      </div>
    </div>

    <div class="publication-summary">
      <span class="publication-eyebrow">DIGITAL MONOGRAPH · PDF 版本</span>
      <h1 id="publication-title">云计算原理与实践：<br><em>以在线游戏为载体</em></h1>
      <p class="publication-abstract">以在线游戏为贯穿案例，从网络通信、单机并发和分布式协同逐步进入云原生部署与核心原理。本页提供高保真完整教材和分章 PDF。</p>
      <dl class="publication-meta">
        <div><dt>版本日期</dt><dd>{edition_date}</dd></div>
        <div><dt>出版单位</dt><dd>湖南大学计算机学院 GuoLab 团队</dd></div>
      </dl>
      <div class="publication-actions">
        <a class="publication-button publication-button-primary" href="{FULL_PDF_PATH}">在线阅读完整教材</a>
        <a class="publication-button publication-button-secondary" href="{FULL_PDF_PATH}" download>下载 PDF</a>
        <a class="publication-text-link" href="{MARKDOWN_URL}">转到 Markdown 正文 →</a>
      </div>
    </div>
  </section>

  <section class="publication-section" aria-labelledby="chapter-heading">
    <header class="publication-section-heading">
      <div>
        <span class="publication-label">TABLE OF CONTENTS</span>
        <h2 id="chapter-heading">正文目录</h2>
      </div>
      <p>按教材目录顺序浏览。每一项均为独立 PDF，可直接打开或另存。</p>
    </header>
    <div class="toc-list">
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
        qmd += f"""      <a class="toc-row" href="chapters/chapter_{key}.pdf">
        <span class="toc-number">{index_label}</span>
        <span class="toc-copy"><strong>{title}</strong><small>{meta} · PDF</small></span>
        <span class="toc-open">打开 PDF</span>
        <span class="toc-arrow" aria-hidden="true">→</span>
      </a>
"""

    qmd += """    </div>
  </section>
"""

    if appendix_cards:
        qmd += """  <section class="publication-section publication-section-compact" aria-labelledby="appendix-heading">
    <header class="publication-section-heading">
      <div>
        <span class="publication-label">SUPPLEMENTARY MATERIAL</span>
        <h2 id="appendix-heading">附录</h2>
      </div>
      <p>重难点索引、实验说明与开源代码导航。</p>
    </header>
    <div class="toc-list">
"""
        for ch in appendix_cards:
            key = ch["key"]
            title = html.escape(ch["title"])
            letter = key.replace("Appendix", "").replace("appendix", "") or "附录"
            qmd += f"""      <a class="toc-row" href="chapters/chapter_{key}.pdf">
        <span class="toc-number">{html.escape(letter)}</span>
        <span class="toc-copy"><strong>{title}</strong><small>补充材料 · PDF</small></span>
        <span class="toc-open">打开 PDF</span>
        <span class="toc-arrow" aria-hidden="true">→</span>
      </a>
"""
        qmd += """    </div>
  </section>
"""

    qmd += f"""  <section class="publication-colophon" aria-label="教材与版权信息">
    <div class="colophon-heading">
      <span class="publication-label">COLOPHON</span>
      <h2>出版与版权信息</h2>
      <p>面向本科云计算课程的持续更新教材。</p>
    </div>
    <div class="colophon-content">
      <div class="colophon-block">
        <h3>教材说明</h3>
        <p>教材以在线游戏为贯穿案例，但所讨论的规模、状态、故障和资源问题同样适用于在线协作、电商平台和大模型服务。</p>
      </div>
      <div class="colophon-block">
        <h3>编者信息</h3>
        <p><a href="https://grzy.hnu.edu.cn/site/index/chenguo">陈果</a>、徐方林、胡文举、庞海鑫、谢先衍、贺臻、张道平<br>湖南大学计算机学院 GuoLab 团队</p>
      </div>
      <div class="colophon-block colophon-license">
        <h3>版权与使用</h3>
        <p>Copyright © 2026 GuoLab. All Rights Reserved. 公开内容可用于个人学习、学术研究和非商业教育实践；完整条款请参阅 <a href="{LICENSE_URL}">LICENSE</a>。</p>
      </div>
    </div>
  </section>
</div>
```
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(qmd)

def generate_compile_sh(chapters, output_path="run_latex.sh"):
    sh_content = """#!/usr/bin/env bash
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
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sh_content)
    os.chmod(output_path, 0o755)


def parse_args():
    parser = argparse.ArgumentParser(description="生成 PDF 站点首页和构建配置")
    parser.add_argument("--source-dir", default="CCBook", help="LaTeX 教材源码目录")
    parser.add_argument("--site-output", default="index.qmd", help="生成的 Quarto 首页路径")
    parser.add_argument("--compile-script-output", default="run_latex.sh", help="兼容用串行编译脚本路径")
    parser.add_argument("--site-only", action="store_true", help="只生成站点首页，不生成串行编译脚本")
    parser.add_argument("--matrix-only", action="store_true", help="只输出 GitHub Actions 章节矩阵 JSON")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    ch_list = extract_chapters(args.source_dir)

    if args.matrix_only:
        matrix = [{"key": ch["key"], "rel_path": ch["rel_path"]} for ch in ch_list]
        print(json.dumps(matrix, ensure_ascii=False, separators=(",", ":")))
    else:
        generate_qmd(ch_list, get_source_metadata(args.source_dir), args.site_output)
        if not args.site_only:
            generate_compile_sh(ch_list, args.compile_script_output)
        print(f"✅ 已生成 {args.site_output}")
