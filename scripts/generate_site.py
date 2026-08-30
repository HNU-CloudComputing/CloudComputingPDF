import argparse
import os
import re
import html
import json

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

def generate_qmd(chapters, output_path="index.qmd"):
    qmd = f"""---
title: "{BOOK_TITLE}"
page-layout: custom
toc: false
title-block-banner: false
---

```{{=html}}
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
    <div class="course-about">
      <span class="course-section-label">ABOUT THE BOOK</span>
      <h2>教材说明</h2>
      <p>教材以在线游戏为贯穿案例，但所讨论的规模、状态、故障和资源问题同样适用于在线协作、电商平台和大模型服务。</p>
    </div>
    <div class="course-editorial-block">
      <span class="course-section-label">EDITORIAL TEAM</span>
      <h2>编者信息</h2>
      <dl class="editorial-list">
        <div><dt>核心编者与架构设计</dt><dd><a href="https://grzy.hnu.edu.cn/site/index/chenguo">陈果</a>、徐方林、胡文举、庞海鑫、谢先衍、贺臻、张道平</dd></div>
        <div><dt>所属单位</dt><dd>湖南大学 HNU GuoLab</dd></div>
        <div><dt>联系邮箱</dt><dd><a href="mailto:guochen@hnu.edu.cn">guochen@hnu.edu.cn</a>、<a href="mailto:xfl825@hnu.edu.cn">xfl825@hnu.edu.cn</a>、<a href="mailto:ashionial@hnu.edu.cn">ashionial@hnu.edu.cn</a></dd></div>
      </dl>
    </div>
    <div class="course-license">
      <span class="course-section-label">COPYRIGHT AND USE</span>
      <h2>版权与使用说明</h2>
      <p class="course-copyright">Copyright © 2026 GuoLab. All Rights Reserved.</p>
      <p>本项目中的文档、示例代码和架构图表均受版权保护。公开内容可用于个人学习、学术研究和非商业教育实践；未经书面许可，不得用于商业产品、付费课程、培训项目或商业出版物。完整条款请参阅 <a href="{LICENSE_URL}">LICENSE</a>。</p>
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
        generate_qmd(ch_list, args.site_output)
        if not args.site_only:
            generate_compile_sh(ch_list, args.compile_script_output)
        print(f"✅ 已生成 {args.site_output}")
