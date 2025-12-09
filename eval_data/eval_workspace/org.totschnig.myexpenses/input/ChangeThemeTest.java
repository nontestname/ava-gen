package org.totschnig.myexpenses.test2va;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.hasDescendant;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.isNotChecked;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;

import androidx.test.ext.junit.rules.ActivityScenarioRule;

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.totschnig.myexpenses.activity.SplashActivity;

public class ChangeThemeTest {

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
    public void changeThemeTest() {
        onView(withContentDescription("More options")).perform(click());
        onView(withText("Settings")).perform(click());
        onView(withText("User interface")).perform(click());
        onView(withText("Theme")).perform(click());
        onView(allOf(withText("Light"), isNotChecked())).perform(click());

        onView(allOf(withText("Light"), withParent(hasDescendant(withText("Theme")))))
                .check(matches(isDisplayed()));
    }
}
