import re
import nltk
import gradio as gr
from nltk.sentiment import SentimentIntensityAnalyzer

# Download VADER lexicon
nltk.download("vader_lexicon", quiet=True)

sia = SentimentIntensityAnalyzer()

# -------------------------------------------------------------------
# Movie-specific sentiment vocabulary
# -------------------------------------------------------------------

POSITIVE_PHRASES = [
    "excellent", "amazing", "brilliant", "fantastic", "superb",
    "great", "good", "beautiful", "impressive", "engaging",
    "enjoyable", "strong", "satisfying", "wonderful", "outstanding",
    "interesting", "pleasant", "solid", "convincing", "promising",
    "improves", "improved", "improves considerably", "gets better",
    "got better", "picks up", "picks up toward", "toward the end",
    "is brisk", "are brisk", "was brisk", "were brisk",
    "keeps the movie moving", "promising premise",
    "convincing performance", "strong performance",
    "delivers a convincing performance", "delivers a strong performance",
    "direction is solid", "looks excellent", "adds some energy",
    "music adds some energy", "good moments"
]

NEGATIVE_PHRASES = [
    "weak", "poor", "bad", "terrible", "awful", "boring",
    "slow", "painfully slow", "predictable", "disappointing",
    "underwhelming", "forgettable", "inconsistent", "uneven",
    "rushed", "uninspired", "dull", "bland", "ordinary",
    "fails to", "not developed enough", "characters are not developed enough",
    "predictable later", "pacing slows down", "slows down in the middle",
    "pacing slows", "disappointing", "feels rushed",
    "falls short of its potential"
]

NEUTRAL_PHRASES = [
    "decent", "average", "okay", "acceptable"
]

# -------------------------------------------------------------------
# Aspect detection
# -------------------------------------------------------------------

ASPECT_KEYWORDS_FINAL = {
    "Acting": [
        "acting", "actor", "actress", "performance", "performances",
        "cast", "supporting cast", "lead actor", "lead actress",
        "performer"
    ],
    "Story": [
        "story", "plot", "premise", "screenplay", "screenwriting",
        "script", "character", "characters", "narrative", "storyline"
    ],
    "Direction": [
        "direction", "director", "directing", "directed"
    ],
    "Pacing": [
        "pacing", "pace", "slow", "slows down", "rushed",
        "fast-paced", "fast paced", "dragged", "dragging",
        "lengthy", "overlong"
    ],
    "Music": [
        "music", "song", "songs", "soundtrack", "score",
        "background score", "bgm"
    ],
    "Cinematography": [
        "cinematography", "visuals", "visual", "camera work",
        "shots", "shot composition", "shot"
    ],
    "Climax": [
        "climax", "ending", "finale", "final act"
    ]
}

SENTIMENT_RATING = {
    "Positive": 8.0,
    "Mixed": 6.0,
    "Neutral": 5.5,
    "Negative": 3.0
}


def split_sentiment_clauses(text):
    """Split around common contrast/concession words."""
    parts = re.split(
        r"\s+(?:but|although|though|however|yet|while)\s+",
        text,
        flags=re.IGNORECASE
    )
    return [part.strip() for part in parts if part.strip()]


def proven_classify_clause(clause):
    lower = clause.lower()

    protected_phrases = [
        "without feeling rushed",
        "without being rushed",
        "without feeling slow",
        "without being slow",
        "doesn't feel rushed",
        "does not feel rushed",
        "doesn't seem rushed",
        "does not seem rushed"
    ]

    for phrase in protected_phrases:
        lower = lower.replace(phrase, "")

    positive_hits = sum(
        1 for phrase in POSITIVE_PHRASES
        if phrase in lower
    )

    negative_hits = sum(
        1 for phrase in NEGATIVE_PHRASES
        if phrase in lower
    )

    neutral_hits = sum(
        1 for phrase in NEUTRAL_PHRASES
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

    if "Positive" in sentiments and "Negative" in sentiments:
        return "Mixed"

    if "Positive" in sentiments and "Neutral" in sentiments:
        return "Mixed"

    if "Negative" in sentiments and "Neutral" in sentiments:
        return "Mixed"

    if "Positive" in sentiments:
        return "Positive"

    if "Negative" in sentiments:
        return "Negative"

    return "Neutral"


def calculate_movie_rating_final(aspect_results):
    if not aspect_results:
        return 5.5

    scores = []

    for data in aspect_results.values():
        sentiment = data.get("sentiment", "Neutral")

        if sentiment in SENTIMENT_RATING:
            scores.append(SENTIMENT_RATING[sentiment])

    if not scores:
        return 5.5

    return round(sum(scores) / len(scores), 1)


def get_movie_verdict_final(rating, aspect_results):
    sentiments = [
        data.get("sentiment")
        for data in aspect_results.values()
    ]

    has_positive = "Positive" in sentiments
    has_negative = "Negative" in sentiments
    has_mixed = "Mixed" in sentiments

    if ((has_positive and has_negative) or has_mixed):
        return "Mixed"

    if rating >= 7.0:
        return "Positive"

    if rating <= 4.5:
        return "Negative"

    return "Mixed"


def get_movie_recommendation_final(rating):
    if rating >= 7.0:
        return "Highly Recommended"

    if rating >= 6.0:
        return "Recommended"

    if rating >= 5.0:
        return "Watch if Interested"

    return "Not Recommended"


def create_movie_summary(aspect_results, rating):
    positive = [
        aspect for aspect, data in aspect_results.items()
        if data["sentiment"] == "Positive"
    ]

    negative = [
        aspect for aspect, data in aspect_results.items()
        if data["sentiment"] == "Negative"
    ]

    mixed = [
        aspect for aspect, data in aspect_results.items()
        if data["sentiment"] == "Mixed"
    ]

    parts = []

    if positive:
        if len(positive) == 1:
            positive_text = positive[0]
        elif len(positive) == 2:
            positive_text = f"{positive[0]} and {positive[1]}"
        else:
            positive_text = ", ".join(positive[:-1]) + f" and {positive[-1]}"

        parts.append(f"The movie's stronger areas are {positive_text}.")

    if mixed:
        if len(mixed) == 1:
            mixed_text = mixed[0]
        elif len(mixed) == 2:
            mixed_text = f"{mixed[0]} and {mixed[1]}"
        else:
            mixed_text = ", ".join(mixed[:-1]) + f" and {mixed[-1]}"

        verb = "is" if len(mixed) == 1 else "are"
        parts.append(f"The {mixed_text} {verb} more mixed.")

    if negative:
        if len(negative) == 1:
            negative_text = negative[0]
        elif len(negative) == 2:
            negative_text = f"{negative[0]} and {negative[1]}"
        else:
            negative_text = ", ".join(negative[:-1]) + f" and {negative[-1]}"

        parts.append(f"The main weaknesses are {negative_text}.")

    if rating >= 7:
        conclusion = "Overall, it is a positive experience and worth watching."
    elif rating >= 5:
        conclusion = (
            "Overall, it is a mixed experience and may work better for "
            "viewers who enjoy this type of film."
        )
    else:
        conclusion = (
            "Overall, the movie is held back by several noticeable weaknesses."
        )

    parts.append(conclusion)

    return " ".join(parts)


def final_movie_analyzer(review_text):
    if not review_text or not review_text.strip():
        return {
            "rating": 5.5,
            "verdict": "Mixed",
            "recommendation": "Watch if Interested",
            "aspects": {},
            "summary": "Please enter a movie review."
        }

    review = review_text.strip()

    aspect_data = {
        aspect: {
            "sentiments": [],
            "phrases": []
        }
        for aspect in ASPECT_KEYWORDS_FINAL
    }

    sentences = re.split(r"(?<=[.!?])\s+", review)

    for sentence in sentences:
        clauses = split_sentiment_clauses(sentence)

        for clause in clauses:
            lower_clause = clause.lower()

            matched_aspects = []

            for aspect, keywords in ASPECT_KEYWORDS_FINAL.items():
                if any(keyword in lower_clause for keyword in keywords):
                    matched_aspects.append(aspect)

            if not matched_aspects:
                continue

            sentiment = proven_classify_clause(clause)

            for aspect in matched_aspects:
                aspect_data[aspect]["sentiments"].append(sentiment)
                aspect_data[aspect]["phrases"].append(clause.strip())

    aspect_results = {}

    for aspect, data in aspect_data.items():
        if not data["sentiments"]:
            continue

        aspect_results[aspect] = {
            "sentiment": combine_aspect_sentiments(data["sentiments"]),
            "phrases": list(dict.fromkeys(data["phrases"]))
        }

    rating = calculate_movie_rating_final(aspect_results)
    verdict = get_movie_verdict_final(rating, aspect_results)
    recommendation = get_movie_recommendation_final(rating)
    summary = create_movie_summary(aspect_results, rating)

    return {
        "rating": rating,
        "verdict": verdict,
        "recommendation": recommendation,
        "aspects": aspect_results,
        "summary": summary
    }


# -------------------------------------------------------------------
# Gradio UI
# -------------------------------------------------------------------

def run_movie_analyzer(review_text):
    if not review_text or not review_text.strip():
        return "Please enter a movie review.", "", ""

    result = final_movie_analyzer(review_text)

    overall = (
        f"⭐ **Rating:** {result['rating']}/10\n\n"
        f"🎭 **Verdict:** {result['verdict']}\n\n"
        f"🍿 **Recommendation:** {result['recommendation']}"
    )

    icons = {
        "Acting": "🎭",
        "Story": "📖",
        "Direction": "🎬",
        "Pacing": "⏱️",
        "Music": "🎵",
        "Cinematography": "📷",
        "Climax": "🔥"
    }

    aspect_lines = []

    for aspect, data in result["aspects"].items():
        icon = icons.get(aspect, "🎬")
        aspect_lines.append(
            f"{icon} **{aspect}:** {data['sentiment']}"
        )

    aspect_output = "\n\n".join(aspect_lines)

    if not aspect_output:
        aspect_output = "No movie aspects detected."

    return overall, aspect_output, result["summary"]


example_review = """The film has a promising premise and the lead actor delivers a convincing performance. The supporting cast is decent, but the characters are not developed enough. The first half is engaging, although the screenplay becomes predictable later. The direction is solid and the cinematography looks excellent. The pacing slows down in the middle, while the music adds some energy to the better scenes. The climax is disappointing and feels rushed. Overall, the movie has good moments but falls short of its potential."""


with gr.Blocks(title="Movie Review Analyzer") as demo:
    gr.Markdown(
        "# 🎬 Movie Review Analyzer\n"
        "Analyze a movie review for overall sentiment and key movie aspects."
    )

    review_input = gr.Textbox(
        label="Movie Review",
        placeholder="Paste your movie review here...",
        lines=10
    )

    with gr.Row():
        analyze_btn = gr.Button("🔍 Analyze Review", variant="primary")
        example_btn = gr.Button("📝 Try Example")
        clear_btn = gr.Button("🧹 Clear")

    gr.Markdown("## 🎯 Overall Result")
    overall_output = gr.Markdown()

    gr.Markdown("## 🎭 Movie Aspects")
    aspect_output = gr.Markdown()

    gr.Markdown("## 📝 Review Summary")
    summary_output = gr.Markdown()

    analyze_btn.click(
        fn=run_movie_analyzer,
        inputs=review_input,
        outputs=[
            overall_output,
            aspect_output,
            summary_output
        ]
    )

    example_btn.click(
        fn=lambda: example_review,
        inputs=None,
        outputs=review_input
    )

    clear_btn.click(
        fn=lambda: "",
        inputs=None,
        outputs=review_input
    )

    clear_btn.click(
        fn=lambda: ("", ""),
        inputs=None,
        outputs=[overall_output, aspect_output]
    )

    clear_btn.click(
        fn=lambda: "",
        inputs=None,
        outputs=summary_output
    )


if __name__ == "__main__":
    demo.launch()
