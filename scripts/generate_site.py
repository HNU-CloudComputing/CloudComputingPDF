import os
import re

CCBOOK_PATH = "CCBook"
MAIN_TEX = os.path.join(CCBOOK_PATH, "main.tex")
TITLE_PATTERN = re.compile(r'\\(?:chapter|section)\*?\{([^}]+)\}')
BOOK_TITLE = "云计算原理与实践：以在线游戏为载体"
BOOK_FILE_STEM = BOOK_TITLE
LICENSE_URL = "https://github.com/HNU-CloudComputing/CloudComputingPDF/blob/main/LICENSE"

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
    qmd = f"# {BOOK_TITLE} {{.unnumbered}}\n\n"
    qmd += """这是由 **GuoLab** 成员倾力编写的教科书。由于高质量排版的需要，目前主要以高保真 PDF 形式呈现。

::: {.callout-note appearance="simple" icon="false"}
## 🚀 离线阅读
"""
    qmd += f"👉 [⬇️ 点击此处下载或全屏查看最新版 PDF](chapters/{BOOK_FILE_STEM}_全书.pdf)\n"
    qmd += """:::

<br>

### 📖 分章在线阅读

*无需下载完整大文件，点击下方区块即可在浏览器中极速在线阅读：*

::: {.grid .mt-3}

::: {.g-col-12 .g-col-md-6}
"""
    qmd += f"[📑 目录在线阅读](chapters/{BOOK_FILE_STEM}_目录.pdf)"
    qmd += "{.btn .btn-outline-dark .w-100 .text-start .shadow-sm}\n:::\n"
    for ch in chapters:
        key, title = ch["key"], ch["title"]
        is_intro = "intro" in key.lower()
        
        # 补齐关键的 .btn 类名，确保 Bootstrap 按钮外框生效
        btn_class = ".btn .btn-outline-dark" if is_intro else ".btn .btn-outline-primary"
        col_class = ".g-col-12 .g-col-md-6" if is_intro else ".g-col-12"
        icon = "💡 " if is_intro else "📖 "
        
        qmd += f"""
::: {{{col_class}}}
[{icon}{title}](chapters/chapter_{key}.pdf){{{btn_class} .w-100 .text-start .shadow-sm}}
:::
"""

    qmd += "\n:::\n"
    qmd += """

## 编者信息

- **核心编者与架构设计：** [陈果](https://grzy.hnu.edu.cn/site/index/chenguo)、徐方林、胡文举、庞海鑫、谢先衍、贺臻、张道平
- **所属单位：** 湖南大学 HNU GuoLab
- **联系邮箱：** `guochen@hnu.edu.cn`、`xfl825@hnu.edu.cn`、`ashionial@hnu.edu.cn`

## 版权与使用说明

Copyright © 2026 GuoLab. All Rights Reserved.

本项目中的文档、示例代码和架构图表均受版权保护。公开内容可用于个人学习、学术研究和非商业教育实践；未经书面许可，不得用于商业产品、付费课程、培训项目或商业出版物。完整条款请参阅 [LICENSE]("""
    qmd += LICENSE_URL + ")。\n"

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
