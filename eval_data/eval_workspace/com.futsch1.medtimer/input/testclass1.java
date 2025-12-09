package com.futsch1.medtimer.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.action.ViewActions.closeSoftKeyboard;
import static androidx.test.espresso.action.ViewActions.replaceText;
import static androidx.test.espresso.action.ViewActions.scrollTo;
import static androidx.test.espresso.action.ViewActions.typeText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withClassName;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.containsStringIgnoringCase;
import static org.hamcrest.Matchers.is;

import android.view.View;
import android.view.ViewGroup;
import android.view.ViewParent;

import androidx.test.espresso.ViewInteraction;
import androidx.test.espresso.matcher.ViewMatchers;
import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.filters.LargeTest;
import androidx.test.rule.GrantPermissionRule;

import com.futsch1.medtimer.MainActivity;
import com.futsch1.medtimer.R;

import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

@LargeTest
@RunWith(AndroidJUnit4.class)
public class testclass1 {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Rule
    public GrantPermissionRule mGrantPermissionRule =
            GrantPermissionRule.grant(
                    "android.permission.POST_NOTIFICATIONS");

    @Test
    public void addNewMedicineTest() {

        onView(allOf(ViewMatchers.withId(R.id.medicinesFragment),
                withContentDescription("Medicine"))).perform(click());

        onView(allOf(withId(R.id.addMedicine), withText("Add medicine"))).perform(click());
        onView(withClassName(containsStringIgnoringCase("EditText")))
                .perform(typeText("Claritin"));

        onView(allOf(withId(android.R.id.button1), withText("OK"))).perform(click());

        onView(allOf(withId(R.id.medicineName), withText("Claritin")))
                .check(matches(isDisplayed()));
    }

    @Test
    public void updateOverviewDisplayEventsTest() {
        onView(allOf(withId(R.id.overviewFragment),
                withContentDescription("Overview"))).perform(click());
        onView(withContentDescription("More options")).perform(click());
        onView(withText("Settings")).perform(click());
        onView(allOf(withText("Overview display events"), withId(android.R.id.title))).perform(click());
        onView(allOf(withText("7 days"), withId(android.R.id.text1),
                withClassName(containsStringIgnoringCase("CheckedTextView")))).perform(click());


        onView(allOf(withId(android.R.id.summary), withText("7 days"),
                withParent(hasDescendant(withText("Overview display events"))))).check(matches(isDisplayed()));

    }

}
