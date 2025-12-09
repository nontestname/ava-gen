package org.totschnig.myexpenses.test2va;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.action.ViewActions.replaceText;
import static androidx.test.espresso.action.ViewActions.swipeLeft;
import static androidx.test.espresso.action.ViewActions.typeText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.isRoot;
import static androidx.test.espresso.matcher.ViewMatchers.withClassName;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.containsString;

import androidx.test.ext.junit.rules.ActivityScenarioRule;

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.totschnig.myexpenses.R;
import org.totschnig.myexpenses.activity.SplashActivity;

public class SwitchingAccountTest {

    @Rule
    public ActivityScenarioRule<SplashActivity> rule = new ActivityScenarioRule<>(SplashActivity.class);

    @Before
    public void setup() {
        //OnboardingActivity
        onView(allOf(withText("Next"),
                isDisplayed())).perform(click());
        onView(allOf(withText("Next"),
                isDisplayed())).perform(click());
        onView(allOf(withText("Get started"),
                isDisplayed())).perform(click());

        // add a new account
        onView(withContentDescription("Open navigation drawer")).perform(click());
        onView(withText("Manage accounts")).perform(click());
        onView(withText("New account")).perform(click());
        onView(allOf(withId(R.id.Label), withClassName(containsString("EditText"))))
                .perform(typeText("Saving Account"));
        onView(allOf(withId(R.id.AmountEditText),
                withParent(withContentDescription("Opening balance"))))
                .perform(replaceText("500"));
        onView(withId(R.id.fab)).perform(click());
    }

    @Test
    public void switchingAccountTest() {

        onView(isRoot()).perform(swipeLeft());

        onView(withText("Saving Account")).check(matches(isDisplayed()));
    }
}
