"""Multilingual & Bilingual Learning Support (English & Bangla + extensible registry)."""

from __future__ import annotations

SUPPORTED_LANGUAGES: dict[str, dict[str, str]] = {
    "en": {
        "name": "English",
        "native_name": "English",
        "course_roadmap": "Course Roadmap",
        "prerequisites": "Prerequisites",
        "learning_objectives": "Learning Objectives",
        "core_explanation": "Core Explanation",
        "real_life_analogy": "Real-Life Analogy",
        "worked_example": "Worked Example",
        "practice_exercise": "Practice Exercise",
        "knowledge_check": "Knowledge Check",
        "rule_to_keep": "Rule to Keep",
        "sources_and_citations": "Verified Sources & Citations",
        "technical_terms": "Technical Terminology",
        "summary": "Summary",
        "explain_back_prompt": "Explain It Back (Active Recall)",
    },
    "bn": {
        "name": "Bangla",
        "native_name": "বাংলা",
        "course_roadmap": "কোর্স রোডম্যাপ (Course Roadmap)",
        "prerequisites": "পূর্বশর্ত (Prerequisites)",
        "learning_objectives": "শেখার উদ্দেশ্য (Learning Objectives)",
        "core_explanation": "মূল ব্যাখ্যা (Core Explanation)",
        "real_life_analogy": "বাস্তব জীবনের উদাহরণ (Real-Life Analogy)",
        "worked_example": "ধাপে ধাপে সমাধান (Worked Example)",
        "practice_exercise": "অনুশীলনী (Practice Exercise)",
        "knowledge_check": "নিজেকে যাচাই করুন (Knowledge Check)",
        "rule_to_keep": "মনে রাখার নিয়ম (Rule to Keep)",
        "sources_and_citations": "যাচাইকৃত উৎস ও রেফারেন্স (Verified Sources & Citations)",
        "technical_terms": "প্রযুক্তিগত পরিভাষা (Technical Terminology)",
        "summary": "সারসংক্ষেপ (Summary)",
        "explain_back_prompt": "নিজের ভাষায় বলুন (Active Recall)",
    },
}

# Built-in bilingual technical glossary examples for English <-> Bangla technical teaching
COMMON_TECH_TERMS_BN: dict[str, dict[str, str]] = {
    "variable": {
        "term_en": "Variable",
        "pronunciation_bn": "ভ্যারিয়েবল",
        "meaning_bn": "মেমোরিতে ডেটা সংরক্ষণের একটি নামযুক্ত স্থান যা প্রোগ্রাম চলাকালীন পরিবর্তিত হতে পারে।",
        "definition_en": "A named storage location in memory that holds a value which can change during program execution.",
        "example": "x = 10  # এখানে 'x' হলো একটি Variable যার মান 10",
    },
    "recursion": {
        "term_en": "Recursion",
        "pronunciation_bn": "রিকার্সন (পুনরাবৃত্ত ফাংশন কল)",
        "meaning_bn": "যখন কোনো ফাংশন নিজের সমস্যার ছোট অংশ সমাধানের জন্য নিজেকেই পুনরায় কল করে এবং একটি Base Case-এ থামে।",
        "definition_en": "A technique where a function calls itself on a smaller subproblem until reaching a base case.",
        "example": "def fact(n): return 1 if n <= 1 else n * fact(n - 1)",
    },
    "subnetting": {
        "term_en": "Subnetting",
        "pronunciation_bn": "সাবনেটিং",
        "meaning_bn": "একটি বড় IP নেটওয়ার্ককে ছোট ছোট যৌক্তিক সাব-নেটওয়ার্কে (Subnet) ভাগ করার প্রক্রিয়া যাতে রাউটিং দক্ষতা ও নিরাপত্তা বাড়ে।",
        "definition_en": "The practice of dividing a single IP network into multiple smaller logical sub-networks.",
        "example": "192.168.1.0/24 কে /26 মাস্ক দিয়ে ৪টি সাবনেটে ভাগ করা (প্রতিটিতে ৬২টি ব্যবহারযোগ্য হোস্ট)।",
    },
    "deadlock": {
        "term_en": "Deadlock",
        "pronunciation_bn": "ডেডলক (অচল অবস্থা)",
        "meaning_bn": "এমন একটি পরিস্থিতি যেখানে দুই বা ততোধিক প্রসেস একে অপরের ধরে রাখা রিসোর্সের জন্য অনির্দিষ্টকাল অপেক্ষা করে থাকে।",
        "definition_en": "A state where a set of processes are permanently blocked because each waits for a resource held by another.",
        "example": "Process A ধরে আছে Lock 1 এবং চায় Lock 2; আবার Process B ধরে আছে Lock 2 এবং চায় Lock 1।",
    },
    "normalization": {
        "term_en": "Database Normalization",
        "pronunciation_bn": "ডাটাবেস নরমালাইজেশন",
        "meaning_bn": "ডাটাবেসের তথ্য পুনরাবৃত্তি (Redundancy) কমানো এবং ডেটার অসঙ্গতি (Update/Insert/Delete Anomaly) দূর করার জন্য টেবিলগুলোকে সুশৃঙ্খলভাবে সাজানোর পদ্ধতি।",
        "definition_en": "Organizing relational database tables to minimize redundancy and prevent data modification anomalies (1NF, 2NF, 3NF, BCNF).",
        "example": "একই টেবিলে বারবার ডিপার্টমেন্টের ঠিকানা না লিখে আলাদা Department টেবিল তৈরি করে Foreign Key ব্যবহার করা।",
    },
    "pointer": {
        "term_en": "Pointer",
        "pronunciation_bn": "পয়েন্টার",
        "meaning_bn": "এমন একটি ভ্যারিয়েবল যা সরাসরি কোনো মান না রেখে অন্য আরেকটি ভ্যারিয়েবলের মেমোরি অ্যাড্রেস সংরক্ষণ করে।",
        "definition_en": "A variable that stores the memory address of another variable.",
        "example": "int x = 42; int *p = &x; // এখানে p হলো x-এর মেমোরি অ্যাড্রেস ধারণকারী Pointer",
    },
}


def register_language(code: str, labels: dict[str, str]) -> None:
    """Register an additional language pack dynamically."""
    base = dict(SUPPORTED_LANGUAGES["en"])
    base.update(labels)
    SUPPORTED_LANGUAGES[code.lower()] = base


def translate_ui(key: str, lang: str = "en") -> str:
    """Return localized section header / UI string for the requested language."""
    lang_pack = SUPPORTED_LANGUAGES.get(lang.lower(), SUPPORTED_LANGUAGES["en"])
    return lang_pack.get(key, SUPPORTED_LANGUAGES["en"].get(key, key))


def format_bilingual_term(
    term_en: str,
    explanation_local: str = "",
    definition_en: str = "",
    example: str = "",
    lang: str = "bn",
) -> str:
    """Format a technical term preserving standard English terminology alongside localized explanation."""
    lookup = COMMON_TECH_TERMS_BN.get(term_en.lower().strip())
    pron_bn = ""
    if lookup and lang.lower() == "bn":
        term_en = lookup["term_en"]
        pron_bn = f"{lookup.get('pronunciation_bn', '')} — " if lookup.get("pronunciation_bn") else ""
        explanation_local = explanation_local or lookup["meaning_bn"]
        definition_en = definition_en or lookup["definition_en"]
        example = example or lookup["example"]
    if lang.lower() == "en":
        lines = [f"- **{term_en}**: {definition_en or explanation_local}"]
        if example:
            lines.append(f"  - *Example*: `{example}`")
        return "\n".join(lines)
    lines = [
        f"- **{term_en}** ({pron_bn}{translate_ui('technical_terms', lang)}):",
        f"  - **সহজ ব্যাখ্যা ({SUPPORTED_LANGUAGES.get(lang, {}).get('native_name', lang)})**: {explanation_local}",
        f"  - **English Definition**: {definition_en}",
    ]
    if example:
        lines.append(f"  - **উদাহরণ (Example)**: `{example}`")
    return "\n".join(lines)
