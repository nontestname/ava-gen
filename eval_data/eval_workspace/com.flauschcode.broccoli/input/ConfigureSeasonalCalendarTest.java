package com.flauschcode.broccoli.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.doesNotExist;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.hasDescendant;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withParentIndex;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;

import androidx.test.espresso.matcher.ViewMatchers;
import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.filters.LargeTest;

import com.flauschcode.broccoli.MainActivity;
import com.flauschcode.broccoli.R;

import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

@LargeTest
@RunWith(AndroidJUnit4.class)
public class ConfigureSeasonalCalendarTest {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Test
    public void configureSeasonalCalendarTest() {
        onView(withContentDescription("Open navigation drawer")).perform(click());
        onView(withId(R.id.nav_settings)).perform(click());

        // set region
        onView(allOf(withId(android.R.id.title), withText("Region")))
                .perform(click());
        onView(allOf(withId(android.R.id.text1), withText("North America (warmer)"))).perform(click());

        // language
        onView(allOf(withId(android.R.id.title), withText("Languages of recipes")))
                .perform(click());
        onView(allOf(withParentIndex(0), withText("English"))).perform(click());
        onView(allOf(withText("OK"), withId(android.R.id.button1))).perform(click());


        onView(withContentDescription("Open navigation drawer")).perform(click());
        onView(withId(R.id.nav_seasons)).perform(click());

        onView(allOf(withId(R.id.seasons_configure), withText("CONFIGURE")))
                .check(doesNotExist());

    }
    
}
