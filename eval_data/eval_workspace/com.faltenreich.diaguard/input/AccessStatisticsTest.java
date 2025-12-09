package com.faltenreich.diaguard.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
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
public class AccessStatisticsTest {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Test
    public void accessStatisticsTest() {
        onView(allOf(withContentDescription("Open Navigator"))).perform(click());

        onView(withId(R.id.nav_statistics)).perform(click());

        onView(withId(R.id.category_spinner)).perform(click());
        onView(allOf(withId(android.R.id.text1), withText("Weight")))
                .perform(click());

        onView(withId(R.id.interval_spinner)).perform(click());
        onView(allOf(withId(android.R.id.text1), withText("Month")))
                .perform(click());


        onView(allOf(withId(android.R.id.text1), withText("Weight")))
                .check(matches(withText("Weight")));
        onView(allOf(withId(android.R.id.text1), withText("Month")))
                .check(matches(withText("Month")));
    }

}
