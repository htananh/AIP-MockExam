import glob
import json
import os
import re

from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))


def clean(text):
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_answer_text(option):
    """Extract letter + body text from a radio span or checkbox option div."""
    letter = ""
    body = ""
    for s in option.find_all("span"):
        style = s.get("style", "")
        cls = " ".join(s.get("class", []))
        if "flex-shrink: 0" in style and not letter:
            letter = s.get_text(" ", strip=True).rstrip(".")
        if "flex-1" in cls and not body:
            body = s.get_text(" ", strip=True)
    if not body:
        body = option.get_text(" ", strip=True)
    body = re.sub(r"^[A-E]\.\s*", "", body)
    return letter, clean(body)


def parse_file(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    questions = []
    # Each question block header contains "Question N:"
    for header in soup.find_all(string=re.compile(r"Question\s+\d+:")):
        block = header.find_parent(
            "div", class_=lambda c: c and "border-[#d1d7dc]" in c
        )
        if block is None:
            continue

        m = re.search(r"Question\s+(\d+):", header)
        qnum = int(m.group(1)) if m else None

        # Status (Correct / Incorrect) sits in the header row
        header_row = header.find_parent("div")
        status = ""
        status_span = header_row.find("span") if header_row else None
        if status_span:
            status = status_span.get_text(strip=True)

        # Answers area (single- or multi-answer)
        area = block.find("div", class_=lambda c: c and "bg-[#f5f7fa]" in c)

        # Question text = <p> siblings preceding the answers area
        qtext = ""
        if area:
            parts = [p.get_text("\n", strip=True) for p in area.find_previous_siblings("p")]
            parts = [p for p in reversed(parts) if p.strip()]
            qtext = clean("\n".join(parts))

        # Options: radio spans (single answer) or option divs (multiple answers)
        answers = []
        correct_letter = []
        if area:
            options = area.find_all("span", attrs={"role": "radio"})
            if not options:
                options = area.find_all(
                    "div", class_=lambda c: c and "group" in c and "gap-2" in c
                )
            for opt in options:
                letter, body = get_answer_text(opt)
                cls = " ".join(opt.get("class", []))
                is_correct = "bg-[#d7f3e7]" in cls
                if is_correct:
                    correct_letter.append(letter)
                answers.append(
                    {"letter": letter, "text": body, "is_correct": is_correct}
                )

        # Explanation block
        explanation = ""
        exp_block = block.find(
            "div", class_=lambda c: c and "bg-neutral-700" in c
        )
        if exp_block:
            inner = exp_block.find_all("div")
            target = inner[0] if inner else exp_block
            explanation = clean(target.get_text("\n", strip=True))

        questions.append(
            {
                "number": qnum,
                "status": status,
                "question": qtext,
                "answers": answers,
                "correct_answers": correct_letter,
                "explanation": explanation,
            }
        )

    questions.sort(key=lambda q: q["number"] or 0)
    return questions


def main():
    # Exclude the app page itself; each remaining .html file is one exam ("đề")
    skip = {"practice.html", "index.html"}
    html_files = sorted(
        p for p in glob.glob(os.path.join(BASE, "*.html"))
        if os.path.basename(p).lower() not in skip
    )

    exams = []
    for i, path in enumerate(html_files, start=1):
        questions = parse_file(path)
        if not questions:
            continue
        base = os.path.splitext(os.path.basename(path))[0]
        # Stable id from filename so saved progress/history survives adding new exams
        slug = re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")[:40]
        exams.append(
            {
                "id": "exam_" + slug,
                "name": f"Đề {i}",
                "source": os.path.basename(path),
                "questions": questions,
            }
        )

    # JSON output (all exams)
    with open(os.path.join(BASE, "exams.json"), "w", encoding="utf-8") as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

    # JS data file consumed by practice.html (avoids file:// CORS)
    with open(os.path.join(BASE, "exams.js"), "w", encoding="utf-8") as f:
        f.write("window.EXAMS = " + json.dumps(exams, ensure_ascii=False) + ";")

    # Readable text output
    lines = []
    for exam in exams:
        lines.append(f"########## {exam['name']} ({exam['source']}) ##########")
        lines.append("")
        for q in exam["questions"]:
            lines.append(f"=== Question {q['number']} ===")
            lines.append(q["question"])
            lines.append("")
            for a in q["answers"]:
                mark = " (CORRECT)" if a["is_correct"] else ""
                lines.append(f"{a['letter']}. {a['text']}{mark}")
            lines.append("")
            lines.append(f"Correct answer(s): {', '.join(q['correct_answers'])}")
            lines.append("")
            lines.append("Explanation:")
            lines.append(q["explanation"])
            lines.append("")
            lines.append("=" * 60)
            lines.append("")

    with open(os.path.join(BASE, "questions.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    total = sum(len(e["questions"]) for e in exams)
    print(f"Parsed {len(exams)} exam(s), {total} questions total")
    print("Wrote exams.json, exams.js and questions.txt")


if __name__ == "__main__":
    main()
