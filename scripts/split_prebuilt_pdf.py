#!/usr/bin/env python3
"""按完整教材 PDF 的一级书签切分分章 PDF，不重新运行 LaTeX。"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from pypdf import PdfReader, PdfWriter


CHAPTERS = [
    ("intro", "前言"),
    ("sec1", "第一章"),
    ("sec2", "第二章"),
    ("sec3", "第三章"),
    ("sec4", "第四章"),
    ("sec5", "第五章"),
    ("sec6", "第六章"),
    ("AppendixA", "章节重难知识点索引"),
    ("AppendixB", "配套实验与开源代码"),
]
FULL_BOOK_NAME = "云计算原理与实践：以在线游戏为载体_全书.pdf"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def top_level_bookmarks(reader):
    bookmarks = []
    for item in reader.outline:
        if isinstance(item, list):
            continue
        page = reader.get_destination_page_number(item) + 1
        bookmarks.append({"title": item.title.strip(), "page": page})
    return bookmarks


def chapter_ranges(reader):
    bookmarks = top_level_bookmarks(reader)
    matched = []
    search_from = 0
    for key, expected_title in CHAPTERS:
        for index in range(search_from, len(bookmarks)):
            item = bookmarks[index]
            if item["title"].startswith(expected_title):
                matched.append({"key": key, **item})
                search_from = index + 1
                break
        else:
            raise ValueError(f"PDF 一级书签中缺少：{expected_title}")

    ranges = []
    for index, item in enumerate(matched):
        end = (
            matched[index + 1]["page"] - 1
            if index + 1 < len(matched)
            else len(reader.pages)
        )
        if end < item["page"]:
            raise ValueError(f"无效章节页码范围：{item}")
        ranges.append({**item, "end": end})
    return ranges


def add_outline_subset(writer, reference_reader, start_page, end_page):
    """把页码落在当前范围内的书签复制到分章 PDF。"""
    def walk(items, parent=None):
        last_created = None
        for item in items:
            if isinstance(item, list):
                walk(item, parent=last_created or parent)
                continue
            absolute_page = reference_reader.get_destination_page_number(item) + 1
            if start_page <= absolute_page <= end_page:
                last_created = writer.add_outline_item(
                    item.title,
                    absolute_page - start_page,
                    parent=parent,
                )
            else:
                last_created = None

    walk(reference_reader.outline)


def split_pdf(input_path, output_dir, outline_source=None):
    reader = PdfReader(str(input_path))
    reference_reader = PdfReader(str(outline_source or input_path))
    if len(reader.pages) != len(reference_reader.pages):
        raise ValueError(
            "内容 PDF 与书签来源 PDF 页数不一致："
            f"{len(reader.pages)} != {len(reference_reader.pages)}"
        )
    ranges = chapter_ranges(reference_reader)
    output_dir.mkdir(parents=True, exist_ok=True)

    full_output = output_dir / FULL_BOOK_NAME
    shutil.copy2(input_path, full_output)

    manifest = {
        "source": input_path.name,
        "source_sha256": sha256(input_path),
        "full_book": FULL_BOOK_NAME,
        "total_pages": len(reader.pages),
        "chapters": [],
    }

    for item in ranges:
        output_name = f'chapter_{item["key"]}.pdf'
        output_path = output_dir / output_name
        writer = PdfWriter()
        writer.append(
            reader,
            pages=(item["page"] - 1, item["end"]),
            import_outline=False,
        )
        add_outline_subset(writer, reference_reader, item["page"], item["end"])
        writer.add_metadata({
            "/Title": item["title"],
            "/Source": input_path.name,
        })
        with output_path.open("wb") as target:
            writer.write(target)
        page_count = len(PdfReader(str(output_path)).pages)
        expected_count = item["end"] - item["page"] + 1
        if page_count != expected_count:
            raise ValueError(
                f"{output_name} 页数异常：{page_count} != {expected_count}"
            )
        manifest["chapters"].append({
            "key": item["key"],
            "title": item["title"],
            "start_page": item["page"],
            "end_page": item["end"],
            "pages": page_count,
            "file": output_name,
            "sha256": sha256(output_path),
        })

    manifest_path = output_dir / "prebuilt-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description="从完整教材 PDF 切分分章 PDF")
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--outline-source",
        type=Path,
        help="提供一级书签和章节边界的原始完整 PDF",
    )
    args = parser.parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if args.outline_source and not args.outline_source.is_file():
        raise FileNotFoundError(args.outline_source)
    manifest = split_pdf(args.input, args.output_dir, args.outline_source)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
