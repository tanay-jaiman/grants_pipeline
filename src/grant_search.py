#!/usr/bin/env python3

import re

from src.config import CATEGORIES

# Find and return object with all relevant information for recipient checking for all possible IRS keywords
def extract_grant_info(grant, ns):
    def get_text(possible_paths):
        for path in possible_paths:
            value = grant.findtext(path, namespaces=ns)
            if value and value.strip():
                return value.strip()

        return "None"

    return {
        "name" : get_text([
            "irs:RecipientBusinessName/irs:BusinessNameLine1Txt",
            "irs:BusinessNameLine1Txt"
        ]),

        "address" : get_text([
            "irs:RecipientUSAddress/irs:AddressLine1Txt",
            "irs:USAddress/irs:AddressLine1Txt"
        ]),

        "city" : get_text([
            "irs:RecipientUSAddress/irs:CityNm",
            "irs:USAddress/irs:CityNm"
        ]),

        "state" : get_text([
            "irs:RecipientUSAddress/irs:StateAbbreviationCd",
            "irs:USAddress/irs:StateAbbreviationCd"
        ]),

        "zip" : get_text([
            "irs:RecipientUSAddress/irs:ZIPCd",
            "irs:USAddress/irs:ZIPCd"
        ]),

        "relationship" : get_text([
            "irs:RecipientRelationshipTxt"
        ]),

        "status" : get_text([
            "irs:RecipientFoundationStatusTxt"
        ]),

        "purpose" : get_text([
            "irs:GrantOrContributionPurposeTxt",
            "irs:PurposeOfGrantTxt"
        ]),

        "amount" : get_text([
            "irs:Amt",
            "irs:CashGrantAmt",
            "irs:GrantAmt"
        ])
    }

STOP_WORDS = {
    "a",
    "an",
    "and",
    "by",
    "for",
    "in",
    "impact",
    "of",
    "or",
    "program",
    "project",
    "social",
    "the",
    "to",
    "with",
    "support",
    "general"
}

RELATED_TERMS = {
    "arts": {"art", "artist", "artists", "culture", "cultural", "museum", "music", "storytelling"},
    "culture": {"art", "arts", "cultural", "history", "museum", "music", "storytelling"},
    "education": {"academic", "children", "internship", "learning", "school", "scholarship", "student", "students", "youth"},
    "environment": {"climate", "conservation", "ecology", "environmental", "habitat", "restoration", "sustainable", "wildlife"},
    "health": {"clinic", "disease", "healthcare", "hospital", "medical", "mental", "wellness"},
    "housing": {"homeless", "shelter"},
    "immigration": {"asylum", "citizenship", "immigrant", "immigrants", "legal", "migrant", "refugee", "refugees"},
    "justice": {"advocacy", "civil", "legal", "rights"},
    "community": {"advocacy", "food", "health", "healthcare", "housing", "local", "outreach", "restoration", "sanitation"},
    "youth": {"children", "school", "student", "students", "teen", "teens"}
}


def categorize_grant(name: str, purpose: str, categories=None):
    categories = categories or CATEGORIES

    # Prefer the explicit grant purpose; recipient names are only a fallback.
    purpose_category = _best_category_match(purpose, categories)

    if purpose_category:
        return purpose_category

    name_category = _best_category_match(name, categories)

    if name_category:
        return name_category

    return "Other"


def _best_category_match(text: str, categories):
    text_tokens = _tokenize(text)

    if not text_tokens:
        return None

    best_category = None
    best_score = 0

    for category in categories:
        category_terms = _category_terms(category)
        score = len(text_tokens & category_terms)

        if _normalize(category) in _normalize(text):
            score += 3

        if score > best_score:
            best_category = category
            best_score = score

    if best_score == 0:
        return None

    return best_category


def _category_terms(category: str):
    terms = set()

    # Start from the configured category words, then add known related terms.
    for token in _tokenize(category):
        terms.add(token)
        terms.update(RELATED_TERMS.get(token, set()))

    return terms


def _tokenize(text: str):
    if not text or text == "None":
        return set()

    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOP_WORDS and len(token) > 1
    }


def _normalize(text: str):
    if not text:
        return ""

    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))
