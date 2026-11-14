"""Ground-truth comparison metrics for image and ASK robustness experiments.

These metrics are evaluation-only: expected payload text is never passed to a
decoder or used to alter extraction. They quantify partial recovery after a
decoder has produced a candidate/symbol stream.
"""
from __future__ import annotations


def levenshtein_distance(expected: str, observed: str) -> int:
    """Return the minimum character-level edit distance."""
    if len(expected) < len(observed):
        expected, observed = observed, expected
    previous = list(range(len(observed) + 1))
    for i, left in enumerate(expected, start=1):
        current = [i]
        for j, right in enumerate(observed, start=1):
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + (left != right),
            ))
        previous = current
    return previous[-1]


def blue_character_metrics(expected: str, observed: str | None) -> dict:
    """Measure partial character recovery for a candidate at the expected length."""
    if observed is None:
        return {
            "candidate_available": False,
            "candidate_length": 0,
            "position_matches": 0,
            "position_accuracy": 0.0,
            "edit_distance": None,
            "normalized_edit_similarity": 0.0,
        }
    distance = levenshtein_distance(expected, observed)
    denominator = max(len(expected), len(observed), 1)
    matches = sum(a == b for a, b in zip(expected, observed))
    return {
        "candidate_available": True,
        "candidate_length": len(observed),
        "position_matches": matches,
        "position_accuracy": matches / denominator,
        "edit_distance": distance,
        "normalized_edit_similarity": 1.0 - distance / denominator,
    }


def expected_ask_symbols(expected_text: str) -> str:
    """Encode ASCII text into the challenge's 8-bit bytes plus space separators."""
    if not expected_text:
        raise ValueError("expected_text must not be empty")
    if any(ord(character) > 0x7F for character in expected_text):
        raise ValueError("Sleepy Alarm expected payload must be ASCII")
    return " ".join(f"{ord(character):08b}" for character in expected_text)


def sleepy_symbol_metrics(expected_text: str, observed_symbols) -> dict:
    """Measure symbol-level, bit-level and separator recovery after decoding."""
    expected = expected_ask_symbols(expected_text)
    observed = "".join(observed_symbols)
    if len(observed) != len(expected):
        raise ValueError(
            f"expected {len(expected)} measured symbols, received {len(observed)}"
        )
    if any(symbol not in {"0", "1", " "} for symbol in observed):
        raise ValueError("observed symbols must contain only '0', '1' or spaces")

    bit_positions = [i for i, symbol in enumerate(expected) if symbol in "01"]
    separator_positions = [i for i, symbol in enumerate(expected) if symbol == " "]
    bit_errors = sum(observed[i] != expected[i] for i in bit_positions)
    separator_true_positives = sum(observed[i] == " " for i in separator_positions)
    separator_false_negatives = len(separator_positions) - separator_true_positives
    separator_false_positives = sum(
        observed[i] == " " for i in bit_positions
    )
    symbol_errors = sum(a != b for a, b in zip(expected, observed))
    predicted_separators = separator_true_positives + separator_false_positives

    return {
        "expected_symbol_count": len(expected),
        "symbol_errors": symbol_errors,
        "symbol_error_rate": symbol_errors / len(expected),
        "bit_count": len(bit_positions),
        "bit_errors": bit_errors,
        "bit_error_rate": bit_errors / len(bit_positions),
        "expected_separators": len(separator_positions),
        "true_positive_separators": separator_true_positives,
        "false_positive_separators": separator_false_positives,
        "false_negative_separators": separator_false_negatives,
        "separator_precision": (
            separator_true_positives / predicted_separators
            if predicted_separators else None
        ),
        "separator_recall": (
            separator_true_positives / len(separator_positions)
            if separator_positions else None
        ),
    }
