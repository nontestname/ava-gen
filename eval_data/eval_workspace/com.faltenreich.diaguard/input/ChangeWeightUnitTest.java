package com.faltenreich.diaguard.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.contrib.RecyclerViewActions.scrollTo;
import static androidx.test.espresso.matcher.ViewMatchers.hasDescendant;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.anything;
import static org.hamcrest.Matchers.is;

import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.filters.LargeTest;

import com.faltenreich.diaguard.R;
import com.faltenreich.diaguard.feature.navigation.MainActivity;

import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

@LargeTest
@RunWith(AndroidJUnit4.class)
public class ChangeWeightUnitTest {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Test
    public void changeWeightUnitTest() {

        onView(withContentDescription("Open Navigator")).perform(click());
        onView(withId(R.id.nav_settings)).perform(click());

        onView(allOf(withText("Units"))).perform(scrollTo());
        onView(withText("Units")).perform(click());
        onView(withText("Weight")).perform(click());

        onView(allOf(withText("Pound")))
                .perform(click());

        onView(allOf(withId(android.R.id.summary), withText("Pound"),
                        withParent(hasDescendant(withText("Weight")))))
                .check(matches(isDisplayed()));

    }

}
