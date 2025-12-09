package org.totschnig.myexpenses.test2va;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.action.ViewActions.replaceText;
import static androidx.test.espresso.action.ViewActions.scrollTo;
import static androidx.test.espresso.action.ViewActions.typeText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.hasDescendant;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.isNotChecked;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.containsString;

import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.filters.LargeTest;

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.totschnig.myexpenses.R;
import org.totschnig.myexpenses.activity.SplashActivity;

@LargeTest
public class AddNewExpenseTest {

    @Rule
    public ActivityScenarioRule rule = new ActivityScenarioRule<>(SplashActivity.class);

    @Before
    public void setup() {
        //OnboardingActivity
        onView(allOf(withText("Next"),
                isDisplayed())).perform(click());
        onView(allOf(withText("Next"),
                isDisplayed())).perform(click());
        onView(allOf(withText("Get started"),
                isDisplayed())).perform(click());
    }

    @Test
    public void addNewExpenseTest() throws InterruptedException {
        onView(allOf(withId(R.id.fab),
                isDisplayed())).perform(click());
        Thread.sleep(1000);
        onView(allOf(withId(R.id.AmountEditText), withParent(allOf(withId(R.id.Amount),
                hasDescendant(allOf(withId(R.id.TaType), isNotChecked())))))).perform(replaceText("20"));
        onView(allOf(withId(R.id.fab), isDisplayed())).perform(click());

        onView(withText(containsString("20"))).check(matches(isDisplayed()));
    }
}
