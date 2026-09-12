from fastapi import FastAPI
from pydantic import BaseModel
import re


app = FastAPI()


# -----------------------------
# SENTIMENT PHRASES
# -----------------------------

POSITIVE_PHRASES = [
    "excellent",
    "amazing",
    "brilliant",
    "fantastic",
    "superb",
    "great",
    "good",
    "beautiful",
    "impressive",
    "engaging",
    "enjoyable",
    "strong",
    "satisfying",
    "wonderful",
    "outstanding",
    "interesting",
    "pleasant",
    "solid",
    "convincing",
    "promising",
    "improves",
    "improved",
    "improves considerably",
    "gets better",
    "got better",
    "picks up",
    "picks up toward",
    "toward the end",
    "is brisk",
    "are brisk",
    "was brisk",
    "were brisk",
    "keeps the movie moving",
    "promising premise",
    "convincing performance",
    "strong performance",
    "delivers a convincing performance",
    "delivers a strong performance",
    "direction is solid",
    "looks excellent",
    "adds some energy",
    "music adds some energy",
    "good moments",
]


NEGATIVE_PHRASES = [
    "weak",
    "poor",
    "bad",
    "terrible",
    "awful",
    "boring",
    "slow",
    "painfully slow",
    "predictable",
    "disappointing",
    "underwhelming",
    "forgettable",
    "inconsistent",
    "uneven",
    "rushed",
    "uninspired",
    "dull",
    "bland",
    "ordinary",
    "fails to",
    "not developed enough",
    "characters are not developed enough",
    "predictable later",
    "pacing slows down",
    "slows down in the middle",
    "pacing slows",
    "feels rushed",
    "falls short of its potential",
]


NEUTRAL_PHRASES = [
    "decent",
    "average",
    "okay",
    "acceptable",
]


# -----------------------------
# MOVIE ASPECTS
# -----------------------------

ASPECT_KEYWORDS = {
    "Acting": [
        "acting",
        "actor",
        "actress",
        "performance",
        "performances",
        "cast",
        "supporting cast",
        "lead actor",
        "lead actress",
        "performer",
    ],

    "Story": [
        "story",
        "plot",
        "premise",
        "screenplay",
        "screenwriting",
        "script",
        "character",
        "characters",
        "narrative",
        "storyline",
    ],

    "Direction": [
        "direction",
        "director",
        "directing",
        "directed",
    ],

    "Pacing": [
        "pacing",
        "pace",
        "slow",
        "slows down",
        "rushed",
        "fast-paced",
        "fast paced",
        "dragged",
        "dragging",
        "lengthy",
        "overlong",
    ],

    "Music": [
        "music",
        "song",
        "songs",
        "soundtrack",
        "score",
        "background score",
        "bgm",
    ],

    "Cinematography": [
        "cinematography",
        "visuals",
        "visual",
        "camera work",
        "shots",
        "shot composition",
        "shot",
    ],

    "Climax": [
        "climax",
        "ending",
        "finale",
        "final act",
    ],
}


# -----------------------------
# RATING VALUES
# -----------------------------

SENTIMENT_RATING = {
    "Positive": 8.0,
    "Mixed": 6.0,
    "Neutral": 5.5,
    "Negative": 3.0,
}


# -----------------------------
# REQUEST MODEL
# -----------------------------

class ReviewRequest(BaseModel):
    review: str = ""


# -----------------------------
# SENTIMENT HELPERS
# -----------------------------

def split_sentiment_clauses(text):
    parts = re.split(
        r"\s+(?:but|although|though|however|yet|while)\s+",
        text,
        flags=re.IGNORECASE,
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def classify_clause(clause):
    lower = clause.lower()

    protected_phrases = [
        "without feeling rushed",
        "without being rushed",
        "without feeling slow",
        "without being slow",
        "doesn't feel rushed",
        "does not feel rushed",
        "doesn't seem rushed",
        "does not seem rushed",
    ]

    for phrase in protected_phrases:
        lower = lower.replace(phrase, "")

    positive_hits = sum(
        1
        for phrase in POSITIVE_PHRASES
        if phrase in lower
    )

    negative_hits = sum(
        1
        for phrase in NEGATIVE_PHRASES
        if phrase in lower
    )

    neutral_hits = sum(
        1
        for phrase in NEUTRAL_PHRASES
        if phrase in lower
    )

    if positive_hits > negative_hits:
        return "Positive"

    if negative_hits > positive_hits:
        return "Negative"

    if neutral_hits:
        return "Neutral"

    return "Neutral"


def combine_aspect_sentiments(sentiments):
    if not sentiments:
        return "Neutral"

    if (
        "Positive" in sentiments
        and "Negative" in sentiments
    ):
        return "Mixed"

    if (
        "Positive" in sentiments
        and "Neutral" in sentiments
    ):
        return "Mixed"

    if (
        "Negative" in sentiments
        and "Neutral" in sentiments
    ):
        return "Mixed"

    if "Positive" in sentiments:
        return "Positive"

    if "Negative" in sentiments:
        return "Negative"

    return "Neutral"


# -----------------------------
# MAIN ANALYZER
# -----------------------------

def analyze_movie(review):

    if not review or not review.strip():
        return {
            "rating": 5.5,
            "verdict": "Mixed",
            "recommendation": "Watch if Interested",
            "aspects": {},
            "summary": "Please enter a movie review.",
        }

    review = review.strip()

    aspect_data = {
        aspect: {
            "sentiments": [],
            "phrases": [],
        }
        for aspect in ASPECT_KEYWORDS
    }

    sentences = re.split(
        r"(?<=[.!?])\s+",
        review,
    )

    for sentence in sentences:

        clauses = split_sentiment_clauses(sentence)

        for clause in clauses:

            lower_clause = clause.lower()

            matched_aspects = []

            for aspect, keywords in ASPECT_KEYWORDS.items():

                if any(
                    keyword in lower_clause
                    for keyword in keywords
                ):
                    matched_aspects.append(aspect)

            if not matched_aspects:
                continue

            sentiment = classify_clause(clause)

            for aspect in matched_aspects:

                aspect_data[aspect]["sentiments"].append(
                    sentiment
                )

                aspect_data[aspect]["phrases"].append(
                    clause.strip()
                )

    aspect_results = {}

    for aspect, data in aspect_data.items():

        if not data["sentiments"]:
            continue

        aspect_results[aspect] = {
            "sentiment": combine_aspect_sentiments(
                data["sentiments"]
            ),
            "phrases": list(
                dict.fromkeys(data["phrases"])
            ),
        }

    # -----------------------------
    # RATING
    # -----------------------------

    scores = [
        SENTIMENT_RATING[data["sentiment"]]
        for data in aspect_results.values()
        if data["sentiment"] in SENTIMENT_RATING
    ]

    if scores:
        rating = round(
            sum(scores) / len(scores),
            1,
        )
    else:
        rating = 5.5

    # -----------------------------
    # VERDICT
    # -----------------------------

    sentiments = [
        data["sentiment"]
        for data in aspect_results.values()
    ]

    if (
        (
            "Positive" in sentiments
            and "Negative" in sentiments
        )
        or "Mixed" in sentiments
    ):
        verdict = "Mixed"

    elif rating >= 7.0:
        verdict = "Positive"

    elif rating <= 4.5:
        verdict = "Negative"

    else:
        verdict = "Mixed"

    # -----------------------------
    # RECOMMENDATION
    # -----------------------------

    if rating >= 7.0:
        recommendation = "Highly Recommended"

    elif rating >= 6.0:
        recommendation = "Recommended"

    elif rating >= 5.0:
        recommendation = "Watch if Interested"

    else:
        recommendation = "Not Recommended"

    # -----------------------------
    # SUMMARY
    # -----------------------------

    positive = [
        aspect
        for aspect, data in aspect_results.items()
        if data["sentiment"] == "Positive"
    ]

    mixed = [
        aspect
        for aspect, data in aspect_results.items()
        if data["sentiment"] == "Mixed"
    ]

    negative = [
        aspect
        for aspect, data in aspect_results.items()
        if data["sentiment"] == "Negative"
    ]

    def list_words(items):

        if len(items) == 1:
            return items[0]

        if len(items) == 2:
            return f"{items[0]} and {items[1]}"

        return (
            ", ".join(items[:-1])
            + f" and {items[-1]}"
        )

    parts = []

    if positive:
        parts.append(
            f"The movie's stronger areas are "
            f"{list_words(positive)}."
        )

    if mixed:
        parts.append(
            f"The {list_words(mixed)} "
            f"{'is' if len(mixed) == 1 else 'are'} "
            f"more mixed."
        )

    if negative:
        parts.append(
            f"The main weaknesses are "
            f"{list_words(negative)}."
        )

    if rating >= 7.0:

        parts.append(
            "Overall, it is a positive experience "
            "and worth watching."
        )

    elif rating >= 5.0:

        parts.append(
            "Overall, it is a mixed experience and "
            "may work better for viewers who enjoy "
            "this type of film."
        )

    else:

        parts.append(
            "Overall, the movie is held back by "
            "several noticeable weaknesses."
        )

    return {
        "rating": rating,
        "verdict": verdict,
        "recommendation": recommendation,
        "aspects": aspect_results,
        "summary": " ".join(parts),
    }


# -----------------------------
# API ROUTES
# -----------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Movie Review Analyzer API is running.",
    }


@app.get("/api")
def api_health():
    return {
        "status": "ok",
        "message": "Movie Review Analyzer API is running.",
    }


@app.post("/api")
def analyze_review(request: ReviewRequest):
    return analyze_movie(request.review)
