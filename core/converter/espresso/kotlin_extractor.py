import re
from typing import List

ESPRESSO_ENTRYPOINTS = ("onView(", "onData(", "onWebView(")


def extract_espresso_calls_from_kotlin_source(source: str) -> List[str]:
    """
    Extract normalized Espresso calls from a Kotlin test source string.

    Returns strings like:
      'onView(allOf(withId(R.id.text), withText("heelo"))).perform(swipeLeft());'
    even if the original code is multi-line and without semicolons.
    """
    lines = source.splitlines()
    calls: List[str] = []
    buffer: List[str] = []
    collecting = False
    paren_balance = 0
    seen_perform = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if not collecting:
            if any(ep in stripped for ep in ESPRESSO_ENTRYPOINTS):
                collecting = True
                buffer = [stripped]
                paren_balance = stripped.count("(") - stripped.count(")")
                seen_perform = ".perform(" in stripped

                # Rare case: whole expression on one line
                if seen_perform and paren_balance <= 0:
                    calls.append(normalize_kotlin_espresso_call(" ".join(buffer)))
                    collecting = False
                    buffer = []
        else:
            buffer.append(stripped)
            paren_balance += stripped.count("(") - stripped.count(")")
            if ".perform(" in stripped:
                seen_perform = True

            # End when parens are balanced back and we've seen perform()
            if seen_perform and paren_balance <= 0:
                joined = " ".join(buffer)
                calls.append(normalize_kotlin_espresso_call(joined))
                collecting = False
                buffer = []

    return calls


def normalize_kotlin_espresso_call(raw: str) -> str:
    """
    Collapse whitespace, join chained calls into a single line, and add a
    trailing semicolon so it fits the Java-style regex in statement_converter.
    """
    # Remove trailing commas (if any in chained calls)
    s = re.sub(r"\s+", " ", raw).strip()

    # Normalize '.perform(' spacing
    s = re.sub(r"\)\s*\.perform\s*\(", ").perform(", s)

    # Kotlin usually has no semicolons; add one for the converter
    if not s.endswith(";"):
        s += ";"
    return s


if __name__ == "__main__":
    # Minimal self-test
    kotlin_source = """
        import androidx.test.ext.junit.runners.AndroidJUnit4
        import org.junit.Test

        class SampleTest {

            @Test
            fun testSwipeText() {
                onView(allOf(withId(R.id.text), withText("heelo")))
                    .perform(swipeLeft())
            }

            @Test
            fun testClickButton() {
                onView(withId(R.id.loginButton))
                    .perform(click())
                onView(allOf(withText("Press"), unsupportedMatcher()))
                    .perform(click())
            }
        }
    """

    calls = extract_espresso_calls_from_kotlin_source(kotlin_source)
    print("Extracted Kotlin Espresso calls:")
    for c in calls:
        print("  ", c)

    # Simple sanity checks
    assert len(calls) == 2
    assert 'onView(allOf(withId(R.id.text), withText("heelo"))).perform(swipeLeft());' in calls[0]
    assert 'onView(withId(R.id.loginButton)).perform(click());' in calls[1]

    print("\nAll Kotlin extractor tests passed.")