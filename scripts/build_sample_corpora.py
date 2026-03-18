"""
Download and organize sample corpora from public domain sources.

Sources:
- Project Gutenberg (novels, plays, essays, poetry)
- King James Bible (public domain)

Run: python scripts/build_sample_corpora.py
"""

import json
import os
import re
import textwrap
import urllib.request
from pathlib import Path

CORPORA_DIR = (
    Path(__file__).resolve().parent.parent
    / "core"
    / "src"
    / "mowen"
    / "data"
    / "sample_corpora"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch_gutenberg(pg_id: int) -> str:
    """Fetch a Project Gutenberg text by ID."""
    url = f"https://www.gutenberg.org/cache/epub/{pg_id}/pg{pg_id}.txt"
    print(f"  Fetching PG#{pg_id} from {url}")
    req = urllib.request.Request(
        url, headers={"User-Agent": "mowen-corpus-builder/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    # Try UTF-8 first, fall back to latin-1
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def strip_gutenberg(text: str) -> str:
    """Remove Project Gutenberg header and footer."""
    # Find start
    for marker in [
        "*** START OF THE PROJECT GUTENBERG",
        "*** START OF THIS PROJECT GUTENBERG",
        "***START OF THE PROJECT GUTENBERG",
        "***START OF THIS PROJECT GUTENBERG",
    ]:
        idx = text.find(marker)
        if idx != -1:
            text = text[text.index("\n", idx) + 1 :]
            break
    # Find end
    for marker in [
        "*** END OF THE PROJECT GUTENBERG",
        "*** END OF THIS PROJECT GUTENBERG",
        "***END OF THE PROJECT GUTENBERG",
        "***END OF THIS PROJECT GUTENBERG",
        "End of the Project Gutenberg",
        "End of Project Gutenberg",
    ]:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break
    return text.strip()


def split_by_regex(
    text: str, pattern: str, min_words: int = 200
) -> list[tuple[str, str]]:
    """Split text by a regex pattern. Returns (heading, body) pairs."""
    parts = re.split(pattern, text)
    results = []
    # parts[0] is before first match, then alternating (match, body)
    i = 1
    while i < len(parts):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if len(body.split()) >= min_words:
            results.append((heading, body))
        i += 2
    return results


def write_doc(directory: Path, filename: str, text: str):
    """Write a document file."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(text, encoding="utf-8")


def sanitize_filename(s: str) -> str:
    """Make a string safe for filenames (ASCII only)."""
    # Normalize common accented characters
    import unicodedata

    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^\w\-]", "_", s).strip("_")[:60]


# ---------------------------------------------------------------------------
# 1. Federalist Papers
# ---------------------------------------------------------------------------


def _roman_to_int(s: str) -> int:
    """Convert Roman numeral to integer."""
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    s = s.upper().strip().rstrip(".")
    total = 0
    prev = 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total


def build_federalist():
    print("\n=== Federalist Papers ===")
    text = fetch_gutenberg(18)
    text = strip_gutenberg(text)

    # Known authorship (scholarly consensus)
    hamilton = {
        1,
        6,
        7,
        8,
        9,
        11,
        12,
        13,
        15,
        16,
        17,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        59,
        60,
        61,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        80,
        81,
        82,
        83,
        84,
        85,
    }
    madison = {10, 14, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48}
    jay = {2, 3, 4, 5, 64}
    hamilton_madison = {18, 19, 20}  # Joint
    disputed = {49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 62, 63}

    # Skip past table of contents — body starts at "THE FEDERALIST.\nNo. I."
    body_start = text.find("THE FEDERALIST.\n")
    if body_start == -1:
        body_start = text.find("THE FEDERALIST.\r\n")
    if body_start != -1:
        text = text[body_start:]

    # Split by paper headers — format is "No. I." (Roman numerals)
    parts = re.split(r"\n(No\.\s+[IVXLCDM]+\.)", text)

    outdir = CORPORA_DIR / "federalist"
    known = []
    unknown = []

    i = 1
    while i < len(parts):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        roman_match = re.search(r"No\.\s+([IVXLCDM]+)", header)
        if roman_match:
            num = _roman_to_int(roman_match.group(1))
            body_clean = body.strip()
            if len(body_clean.split()) < 100 or num < 1 or num > 85:
                i += 2
                continue

            fname = f"federalist_{num:02d}.txt"
            write_doc(outdir, fname, body_clean)

            if num in hamilton:
                known.append({"file": f"federalist/{fname}", "author": "Hamilton"})
            elif num in madison:
                known.append({"file": f"federalist/{fname}", "author": "Madison"})
            elif num in jay:
                known.append({"file": f"federalist/{fname}", "author": "Jay"})
            elif num in hamilton_madison:
                known.append(
                    {"file": f"federalist/{fname}", "author": "Hamilton & Madison"}
                )
            elif num in disputed:
                unknown.append(
                    {"file": f"federalist/{fname}", "true_author": "Madison"}
                )
        i += 2

    print(f"  {len(known)} known, {len(unknown)} unknown documents")
    return {
        "id": "federalist_papers",
        "name": "Federalist Papers",
        "description": f"Hamilton vs. Madison vs. Jay. {len(known)} papers with known authorship, {len(unknown)} disputed papers (scholarly consensus: Madison). The foundational stylometry problem.",
        "known": known,
        "unknown": unknown,
    }


# ---------------------------------------------------------------------------
# 2. Shakespeare vs. Contemporaries
# ---------------------------------------------------------------------------


def build_shakespeare():
    print("\n=== Shakespeare vs. Contemporaries ===")

    # Last play per author held out as unknown
    plays = {
        "Shakespeare": [
            (1533, "Hamlet"),
            (1524, "Macbeth"),
            (1531, "King Lear"),
            (1532, "Othello"),
            (1534, "Romeo and Juliet"),  # known
            (1514, "A Midsummer Night's Dream"),  # held out
        ],
        "Marlowe": [
            (811, "Doctor Faustus"),
            (1094, "Edward the Second"),  # known
            (1589, "The Jew of Malta"),  # held out
        ],
        "Jonson": [
            (5333, "Volpone"),  # known
            (3694, "Every Man in His Humour"),  # held out
        ],
    }

    # Which plays to hold out (last per author)
    holdout = {
        "A Midsummer Night's Dream",
        "The Jew of Malta",
        "Every Man in His Humour",
    }

    outdir = CORPORA_DIR / "shakespeare"
    known = []
    unknown = []

    for author, play_list in plays.items():
        for pg_id, title in play_list:
            try:
                text = fetch_gutenberg(pg_id)
                text = strip_gutenberg(text)
                if len(text.split()) < 500:
                    print(f"  Skipping {title} (too short)")
                    continue
                fname = f"{sanitize_filename(author)}_{sanitize_filename(title)}.txt"
                write_doc(outdir, fname, text)
                if title in holdout:
                    unknown.append(
                        {"file": f"shakespeare/{fname}", "true_author": author}
                    )
                else:
                    known.append({"file": f"shakespeare/{fname}", "author": author})
            except Exception as e:
                print(f"  Failed to fetch {title}: {e}")

    # Henry VIII as unknown (Shakespeare/Fletcher collaboration)
    try:
        text = fetch_gutenberg(1539)
        text = strip_gutenberg(text)
        fname = "unknown_Henry_VIII.txt"
        write_doc(outdir, fname, text)
        unknown.append(
            {"file": f"shakespeare/{fname}", "true_author": "Shakespeare & Fletcher"}
        )
    except Exception as e:
        print(f"  Failed to fetch Henry VIII: {e}")

    print(f"  {len(known)} known, {len(unknown)} unknown documents")
    return {
        "id": "shakespeare_contemporaries",
        "name": "Shakespeare vs. Contemporaries",
        "description": f"Shakespeare, Marlowe, and Jonson. {len(known)} plays with known authorship, {len(unknown)} held out (including the disputed Henry VIII).",
        "known": known,
        "unknown": unknown,
    }


# ---------------------------------------------------------------------------
# 3. Brontë Sisters
# ---------------------------------------------------------------------------


def split_into_chapters(text: str) -> list[tuple[str, str]]:
    """Split a novel into chapters."""
    # Try common chapter heading patterns
    for pattern in [
        r"(CHAPTER\s+[IVXLCDM\d]+[^\n]*)",
        r"(Chapter\s+[IVXLCDM\d]+[^\n]*)",
    ]:
        parts = split_by_regex(text, pattern, min_words=300)
        if len(parts) >= 3:
            return parts
    return []


def build_brontes():
    print("\n=== Brontë Sisters ===")

    novels = {
        "Charlotte Brontë": [(1260, "Jane Eyre")],
        "Emily Brontë": [(768, "Wuthering Heights")],
        "Anne Brontë": [(767, "Agnes Grey"), (969, "Tenant of Wildfell Hall")],
    }

    outdir = CORPORA_DIR / "brontes"
    known = []
    unknown = []

    # Collect all chapters per author, then hold out last 2
    author_chapters: dict[str, list[tuple[str, str, str]]] = (
        {}
    )  # author -> [(fname, body, title)]

    for author, novel_list in novels.items():
        if author not in author_chapters:
            author_chapters[author] = []
        for pg_id, title in novel_list:
            try:
                text = fetch_gutenberg(pg_id)
                text = strip_gutenberg(text)
                chapters = split_into_chapters(text)
                if not chapters:
                    fname = (
                        f"{sanitize_filename(author)}_{sanitize_filename(title)}.txt"
                    )
                    author_chapters[author].append((fname, text, title))
                else:
                    step = max(1, len(chapters) // 8)
                    selected = chapters[::step][:8]
                    for j, (heading, body) in enumerate(selected):
                        fname = f"{sanitize_filename(author)}_{sanitize_filename(title)}_ch{j+1:02d}.txt"
                        author_chapters[author].append((fname, body, title))
            except Exception as e:
                print(f"  Failed to fetch {title}: {e}")

    for author, chapters in author_chapters.items():
        # Hold out last 2 chapters as unknowns
        n_holdout = min(2, max(1, len(chapters) // 4))
        for i, (fname, body, title) in enumerate(chapters):
            write_doc(outdir, fname, body)
            if i >= len(chapters) - n_holdout:
                unknown.append({"file": f"brontes/{fname}", "true_author": author})
            else:
                known.append({"file": f"brontes/{fname}", "author": author})

    print(f"  {len(known)} known, {len(unknown)} unknown documents")
    return {
        "id": "bronte_sisters",
        "name": "Brontë Sisters",
        "description": f"Charlotte, Emily, and Anne Brontë. {len(known)} chapter excerpts with known authorship, {len(unknown)} held out for attribution. Similar upbringing and genre but distinct styles.",
        "known": known,
        "unknown": unknown,
    }


# ---------------------------------------------------------------------------
# 4. Pauline Epistles
# ---------------------------------------------------------------------------

# KJV text for the epistles (public domain)
PAULINE_EPISTLES = {
    # Undisputed
    "Romans": 1028,
    "1 Corinthians": 1029,
    "2 Corinthians": 1030,
    "Galatians": 1031,
    "Philippians": 1033,
    "1 Thessalonians": 1035,
    "Philemon": 1040,
    # Disputed
    "Ephesians": 1032,
    "Colossians": 1034,
    "2 Thessalonians": 1036,
    # Pastoral (likely not Paul)
    "1 Timothy": 1037,
    "2 Timothy": 1038,
    "Titus": 1039,
}

# Known: undisputed Paul + pastoral (as second author class "Pastoral")
# Unknown: the 3 disputed letters (Ephesians, Colossians, 2 Thessalonians)
UNDISPUTED = {
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Philippians",
    "1 Thessalonians",
    "Philemon",
}
PASTORAL = {"1 Timothy", "2 Timothy", "Titus"}
DISPUTED = {"Ephesians", "Colossians", "2 Thessalonians"}


def build_pauline():
    print("\n=== Pauline Epistles ===")
    # Fetch KJV Bible from Gutenberg
    text = fetch_gutenberg(10)
    text = strip_gutenberg(text)

    outdir = CORPORA_DIR / "pauline"
    known = []
    unknown = []

    kjv_names = [
        ("Romans", "The Epistle of Paul the Apostle to the Romans"),
        ("1 Corinthians", "The First Epistle of Paul the Apostle to the Corinthians"),
        ("2 Corinthians", "The Second Epistle of Paul the Apostle to the Corinthians"),
        ("Galatians", "The Epistle of Paul the Apostle to the Galatians"),
        ("Ephesians", "The Epistle of Paul the Apostle to the Ephesians"),
        ("Philippians", "The Epistle of Paul the Apostle to the Philippians"),
        ("Colossians", "The Epistle of Paul the Apostle to the Colossians"),
        (
            "1 Thessalonians",
            "The First Epistle of Paul the Apostle to the Thessalonians",
        ),
        (
            "2 Thessalonians",
            "The Second Epistle of Paul the Apostle to the Thessalonians",
        ),
        ("1 Timothy", "The First Epistle of Paul the Apostle to Timothy"),
        ("2 Timothy", "The Second Epistle of Paul the Apostle to Timothy"),
        ("Titus", "The Epistle of Paul to Titus"),
        ("Philemon", "The Epistle of Paul to Philemon"),
    ]

    # Build an ordered list of (epistle_name, body_position) using the LAST
    # occurrence of each header (first is the TOC entry)
    positions = []
    for epistle, header in kjv_names:
        # Find the last occurrence (body, not TOC)
        pos = text.rfind(header)
        if pos != -1:
            positions.append((epistle, header, pos))
        else:
            print(f"  Could not find {epistle} in KJV text")

    # Sort by position so we can use the next header as boundary
    positions.sort(key=lambda x: x[2])

    # Also find the boundary after the last epistle
    hebrews_pos = text.rfind("The Epistle of Paul the Apostle to the Hebrews")
    if hebrews_pos == -1:
        hebrews_pos = text.rfind("The General Epistle")

    for idx, (epistle, header, start) in enumerate(positions):
        # End boundary is the start of the next epistle, or Hebrews
        if idx + 1 < len(positions):
            end = positions[idx + 1][2]
        elif hebrews_pos != -1 and hebrews_pos > start:
            end = hebrews_pos
        else:
            end = len(text)

        epistle_text = text[start:end].strip()
        if len(epistle_text.split()) < 50:
            print(
                f"  {epistle} too short ({len(epistle_text.split())} words), skipping"
            )
            continue

        fname = f"{sanitize_filename(epistle)}.txt"
        write_doc(outdir, fname, epistle_text)

        if epistle in UNDISPUTED:
            known.append({"file": f"pauline/{fname}", "author": "Paul"})
        elif epistle in PASTORAL:
            known.append({"file": f"pauline/{fname}", "author": "Pastoral"})
        elif epistle in DISPUTED:
            unknown.append({"file": f"pauline/{fname}", "true_author": "NONE"})

    print(f"  {len(known)} known, {len(unknown)} unknown documents")
    return {
        "id": "pauline_epistles",
        "name": "Pauline Epistles",
        "description": f"Paul vs. Pastoral author (KJV). {len(known)} letters with known attribution (undisputed Paul + pastoral), {len(unknown)} genuinely disputed letters (Ephesians, Colossians, 2 Thessalonians).",
        "known": known,
        "unknown": unknown,
    }


# ---------------------------------------------------------------------------
# 5. State of the Union Addresses
# ---------------------------------------------------------------------------


def build_sotu():
    print("\n=== State of the Union Addresses ===")

    # Last address per president held out as unknown
    presidents = {
        "Abraham Lincoln": [
            (34901, "1861 SOTU"),
            (34902, "1862 SOTU"),
            (34903, "1863 SOTU"),
            (34904, "1864 SOTU"),  # held out
        ],
        "Theodore Roosevelt": [
            (5032, "1901 SOTU"),
            (5033, "1902 SOTU"),
            (5034, "1903 SOTU"),  # held out
        ],
        "Woodrow Wilson": [
            (5042, "1913 SOTU"),
            (5043, "1914 SOTU"),
            (5044, "1915 SOTU"),  # held out
        ],
    }

    holdout_titles = {"1864 SOTU", "1903 SOTU", "1915 SOTU"}

    outdir = CORPORA_DIR / "sotu"
    known = []
    unknown = []

    for author, addresses in presidents.items():
        for pg_id, title in addresses:
            try:
                text = fetch_gutenberg(pg_id)
                text = strip_gutenberg(text)
                if len(text.split()) < 200:
                    print(f"  Skipping {title} (too short)")
                    continue
                fname = f"{sanitize_filename(author)}_{sanitize_filename(title)}.txt"
                write_doc(outdir, fname, text)
                if title in holdout_titles:
                    unknown.append({"file": f"sotu/{fname}", "true_author": author})
                else:
                    known.append({"file": f"sotu/{fname}", "author": author})
            except Exception as e:
                print(f"  Failed to fetch {title}: {e}")

    print(f"  {len(known)} known, {len(unknown)} unknown documents")
    return {
        "id": "state_of_the_union",
        "name": "State of the Union Addresses",
        "description": f"Lincoln, T. Roosevelt, and Wilson. {len(known)} addresses with known authorship, {len(unknown)} held out for attribution.",
        "known": known,
        "unknown": unknown,
    }


# ---------------------------------------------------------------------------
# 6. Satoshi Nakamoto
# ---------------------------------------------------------------------------


def build_satoshi():
    print("\n=== Satoshi Nakamoto ===")
    # The Bitcoin whitepaper is freely available and widely redistributed
    # We'll include key sections as documents
    # Forum posts are publicly archived but we'll use the whitepaper sections

    outdir = CORPORA_DIR / "satoshi"
    known = []
    unknown = []

    # We can't reliably download all needed texts here, so create a stub
    # with instructions. The whitepaper is available but forum posts
    # and candidate writings need careful curation.
    readme = textwrap.dedent("""\
        Satoshi Nakamoto Corpus
        =======================

        This corpus requires manual curation due to the nature of the texts.

        Suggested structure:
        - known/: Writings by candidate authors (Nick Szabo's blog posts,
          Hal Finney's forum posts, Wei Dai's b-money paper, etc.)
        - unknown/: Satoshi's Bitcoin whitepaper sections and forum posts

        Sources:
        - Bitcoin whitepaper: bitcoin.org/bitcoin.pdf
        - Satoshi's forum posts: bitcointalk.org (archived)
        - Nick Szabo: unenumerated.blogspot.com
        - Hal Finney: various forum archives
    """)
    write_doc(outdir, "README.txt", readme)
    print("  Created stub — requires manual curation")
    return None  # Skip manifest entry for now


# ---------------------------------------------------------------------------
# 7. Russian Literature
# ---------------------------------------------------------------------------


def build_russian():
    print("\n=== Russian Literature ===")

    novels = {
        "Dostoevsky": [
            (2554, "Crime and Punishment"),
            (28054, "The Brothers Karamazov"),
        ],
        "Tolstoy": [
            (2600, "War and Peace"),
            (1399, "Anna Karenina"),
        ],
        "Chekhov": [
            (1732, "The Lady with the Dog and Other Stories"),
        ],
        "Turgenev": [
            (30723, "Fathers and Sons"),
        ],
    }

    outdir = CORPORA_DIR / "russian_lit"
    # Collect all chapters per author, then hold out last one
    author_docs: dict[str, list[tuple[str, str]]] = {}  # author -> [(fname, body)]

    for author, novel_list in novels.items():
        if author not in author_docs:
            author_docs[author] = []
        for pg_id, title in novel_list:
            try:
                text = fetch_gutenberg(pg_id)
                text = strip_gutenberg(text)
                chapters = split_into_chapters(text)
                if not chapters:
                    stories = split_by_regex(
                        text, r"\n\n([A-Z][A-Z ]{3,}[A-Z])\n\n", min_words=500
                    )
                    if stories:
                        chapters = stories
                    else:
                        fname = f"{sanitize_filename(author)}_{sanitize_filename(title)}.txt"
                        author_docs[author].append((fname, text))
                        continue
                step = max(1, len(chapters) // 6)
                selected = chapters[::step][:6]
                for j, (heading, body) in enumerate(selected):
                    fname = f"{sanitize_filename(author)}_{sanitize_filename(title)}_ch{j+1:02d}.txt"
                    author_docs[author].append((fname, body))
            except Exception as e:
                print(f"  Failed to fetch {title}: {e}")

    known = []
    unknown = []
    for author, docs in author_docs.items():
        for i, (fname, body) in enumerate(docs):
            write_doc(outdir, fname, body)
            if i == len(docs) - 1:  # hold out last doc per author
                unknown.append({"file": f"russian_lit/{fname}", "true_author": author})
            else:
                known.append({"file": f"russian_lit/{fname}", "author": author})

    print(f"  {len(known)} known, {len(unknown)} unknown documents")
    return {
        "id": "russian_literature",
        "name": "Russian Literature",
        "description": f"Dostoevsky, Tolstoy, Chekhov, and Turgenev in English translation. {len(known)} chapter excerpts with known authorship, {len(unknown)} held out for attribution.",
        "known": known,
        "unknown": unknown,
    }


# ---------------------------------------------------------------------------
# 8. Supreme Court Opinions
# ---------------------------------------------------------------------------


def build_scotus():
    print("\n=== Supreme Court Opinions ===")
    # Supreme Court opinions are harder to get from Gutenberg
    # Create a stub with instructions for sourcing from CourtListener
    outdir = CORPORA_DIR / "scotus"
    readme = textwrap.dedent("""\
        Supreme Court Opinions Corpus
        ==============================

        This corpus requires sourcing from public legal databases.

        Suggested sources:
        - CourtListener (courtlistener.com) - bulk data API
        - Supreme Court website (supremecourt.gov)

        Suggested justices (distinctive styles):
        - Antonin Scalia
        - Ruth Bader Ginsburg
        - John Roberts
        - Clarence Thomas
        - Elena Kagan
    """)
    write_doc(outdir, "README.txt", readme)
    print("  Created stub — requires manual curation")
    return None


# ---------------------------------------------------------------------------
# 9. Homeric Question
# ---------------------------------------------------------------------------


def build_homer():
    print("\n=== Homeric Question ===")

    outdir = CORPORA_DIR / "homer"
    known = []
    unknown = []

    # Hold out books 8, 16, 24 from each epic (evenly spaced through the text)
    holdout_books = {8, 16, 24}

    # Iliad - Samuel Butler translation (PG#2199)
    # Odyssey - Samuel Butler translation (PG#1727)
    for pg_id, title in [(2199, "Iliad"), (1727, "Odyssey")]:
        try:
            text = fetch_gutenberg(pg_id)
            text = strip_gutenberg(text)
            books = split_by_regex(text, r"(BOOK\s+[IVXLCDM]+[^\n]*)", min_words=300)
            if not books:
                fname = f"Homer_{sanitize_filename(title)}.txt"
                write_doc(outdir, fname, text)
                known.append({"file": f"homer/{fname}", "author": title})
            else:
                for j, (heading, body) in enumerate(books):
                    book_num = j + 1
                    fname = f"Homer_{sanitize_filename(title)}_book{book_num:02d}.txt"
                    write_doc(outdir, fname, body)
                    if book_num in holdout_books:
                        unknown.append({"file": f"homer/{fname}", "true_author": title})
                    else:
                        known.append({"file": f"homer/{fname}", "author": title})
        except Exception as e:
            print(f"  Failed to fetch {title}: {e}")

    print(f"  {len(known)} known, {len(unknown)} unknown documents")
    return {
        "id": "homeric_question",
        "name": "The Homeric Question",
        "description": f"Iliad vs. Odyssey (Butler translation), split by book. {len(known)} books with known attribution, {len(unknown)} held out. Tests whether the same author composed both epics — also suitable for authorship diarization research.",
        "known": known,
        "unknown": unknown,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("Building sample corpora...")
    print(f"Output: {CORPORA_DIR}")

    # Load existing manifest
    manifest_path = CORPORA_DIR / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        # Keep existing AAAC entries
        existing_ids = {e["id"] for e in manifest}
    else:
        manifest = []
        existing_ids = set()

    builders = [
        build_federalist,
        build_shakespeare,
        build_brontes,
        build_pauline,
        build_sotu,
        build_satoshi,
        build_russian,
        build_scotus,
        build_homer,
    ]

    for builder in builders:
        try:
            entry = builder()
            if entry is not None:
                # Remove old entry with same ID if exists
                manifest = [e for e in manifest if e["id"] != entry["id"]]
                manifest.append(entry)
        except Exception as e:
            print(f"  ERROR: {e}")

    # Write manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n=== Summary ===")
    for entry in manifest:
        n_known = len(entry.get("known", []))
        n_unknown = len(entry.get("unknown", []))
        print(f"  {entry['id']}: {n_known} known, {n_unknown} unknown")
    print(f"\nTotal: {len(manifest)} corpora in manifest")


if __name__ == "__main__":
    main()
