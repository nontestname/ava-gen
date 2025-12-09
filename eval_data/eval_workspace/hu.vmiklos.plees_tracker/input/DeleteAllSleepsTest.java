package hu.vmiklos.plees_tracker.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.action.ViewActions.swipeLeft;
import static androidx.test.espresso.assertion.ViewAssertions.doesNotExist;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isClickable;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withParentIndex;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;

import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.filters.LargeTest;

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

import hu.vmiklos.plees_tracker.MainActivity;
import hu.vmiklos.plees_tracker.R;

@LargeTest
@RunWith(AndroidJUnit4.class)
public class DeleteAllSleepsTest {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Before
    public void before() throws InterruptedException {
        Thread.sleep(2000);

        onView(allOf(withId(R.id.start_stop_text), withText("Start"))).perform(click());
        Thread.sleep(2000);
        onView(allOf(withId(R.id.start_stop_text), withText("Stop"))).perform(click());

        onView(allOf(withId(R.id.start_stop_text), withText("Start"))).perform(click());
        Thread.sleep(2000);
        onView(allOf(withId(R.id.start_stop_text), withText("Stop"))).perform(click());

        onView(allOf(withId(R.id.start_stop_text), withText("Start"))).perform(click());
        Thread.sleep(2000);
        onView(allOf(withId(R.id.start_stop_text), withText("Stop"))).perform(click());
    }

    @Test
    public void deleteAllSleepsTest() throws InterruptedException {
        Thread.sleep(1000);
        onView(withContentDescription("More options")).perform(click());
        onView(withText("Delete All Sleep")).perform(click());
        onView(allOf(withText("YES"), withId(android.R.id.button1))).perform(click());

        onView(withId(R.id.no_sleeps)).check(matches(isDisplayed()));
    }


}
