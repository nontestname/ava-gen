import re
from typing import List

ESPRESSO_ENTRYPOINTS = ("onView(", "onData(", "onWebView(")


def extract_espresso_calls_from_java_source(source: str) -> List[str]:
    """
    Extract normalized Espresso calls from a Java test source string.

    Returns strings like:
      'onView(allOf(withId(R.id.text), withText(heelo))).perform(swipeLeft());'
    """
    lines = source.splitlines()
    calls: List[str] = []
    buffer: List[str] = []
    collecting = False
    paren_balance = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if not collecting:
            # Look for start of an Espresso expression
            if any(ep in stripped for ep in ESPRESSO_ENTRYPOINTS):
                collecting = True
                buffer = [stripped]
                paren_balance = stripped.count("(") - stripped.count(")")
                # If everything is on one line already
                if ".perform(" in stripped and stripped.rstrip().endswith(");") and paren_balance <= 0:
                    calls.append(normalize_java_espresso_call(" ".join(buffer)))
                    collecting = False
                    buffer = []
        else:
            # We are collecting continuation lines of the same Espresso call
            buffer.append(stripped)
            paren_balance += stripped.count("(") - stripped.count(")")
            joined = " ".join(buffer)

            # Heuristic end: we saw .perform( and expression ends with ');
            if ".perform(" in joined and joined.rstrip().endswith(");") and paren_balance <= 0:
                calls.append(normalize_java_espresso_call(joined))
                collecting = False
                buffer = []

    return calls


def normalize_java_espresso_call(raw: str) -> str:
    """
    Collapse whitespace and ensure a trailing semicolon, without changing
    Espresso structure. This prepares the string for statement_converter.
    """
    # Collapse internal whitespace
    s = re.sub(r"\s+", " ", raw).strip()

    # Ensure single spaces around .perform if you like (optional)
    s = re.sub(r"\)\s*\.perform\s*\(", ").perform(", s)

    # Ensure trailing semicolon
    if not s.endswith(";"):
        s += ";"
    return s


if __name__ == "__main__":
    # Minimal self-test
    java_source = """
        import androidx.test.ext.junit.runners.AndroidJUnit4;
        import org.junit.Test;

        public class SampleTest {

            @Test
            public void testSwipeText() {
                onView(allOf(withId(R.id.text), withText("heelo"))).perform(swipeLeft());
            }

            @Test
            public void testClickButton() {
                onView(withId(R.id.loginButton)).perform(click());
                onView(allOf(withText("Press"), unsupportedMatcher())).perform(click());
            }
        }
    """

    calls = extract_espresso_calls_from_java_source(java_source)
    print("Extracted Java Espresso calls:")
    for c in calls:
        print("  ", c)

    # Simple sanity checks
    assert len(calls) == 3
    assert "onView(allOf(withId(R.id.text), withText(\"heelo\"))).perform(swipeLeft());" in calls[0]
    assert "onView(withId(R.id.loginButton)).perform(click());" in calls[1]

    print("\nAll Java extractor tests passed.")