#!/usr/bin/env python3

# Find and return object with all relevant information for recipient checking for all possible IRS keywords
def extract_grant_info(grant, ns):
    def get_text(possible_paths):
        for path in possible_paths:
            value = grant.findtext(path, namespaces=ns)
            if value and value.strip():
                return value.strip()

        return None

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

def categorize_purpose(purpose: str):

    if not purpose:
        return "Other"

    text = purpose.lower()

    # Immigration Support
    immigration_keywords = [
        "immigration",
        "asylum",
        "migrant",
        "refugee",
        "legal services",
        "citizenship"
    ]

    # Education & Youth Development
    education_keywords = [
        "education",
        "school",
        "student",
        "youth",
        "scholarship",
        "internship",
        "learning",
        "children",
        "academic"
    ]

    # Arts, Culture, and Social Impact
    arts_keywords = [
        "arts",
        "culture",
        "museum",
        "music",
        "history",
        "storytelling",
        "community arts",
        "oral history"
    ]

    # Community Empowerment
    community_keywords = [
        "community",
        "housing",
        "food",
        "health",
        "empowerment",
        "environment",
        "restoration",
        "support",
        "advocacy",
        "sanitation"
    ]

    if any(word in text for word in immigration_keywords):
        return "Immigration Support"

    if any(word in text for word in education_keywords):
        return "Education & Youth Development"

    if any(word in text for word in arts_keywords):
        return "Arts, Culture, and Social Impact"

    if any(word in text for word in community_keywords):
        return "Community Empowerment"

    return "Other"