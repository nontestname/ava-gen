package hu.vmiklos.plees_tracker.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.hasDescendant;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;

import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.filters.LargeTest;

import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

import hu.vmiklos.plees_tracker.MainActivity;
import hu.vmiklos.plees_tracker.R;

@LargeTest
@RunWith(AndroidJUnit4.class)
public class UpdateReportDurationTest {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Test
    public void updateReportDurationTest() {

        onView(withContentDescription("More options")).perform(click());
        onView(allOf(withText("Settings"), withId(R.id.title))).perform(click());
        onView(allOf(withText("Duration"), withId(android.R.id.title))).perform(click());
        onView(withText("Last month")).perform(click());

        onView(allOf(withText("Last month"), withParent(hasDescendant(withText("Duration")))))
                .check(matches(isDisplayed()));
    }


}
