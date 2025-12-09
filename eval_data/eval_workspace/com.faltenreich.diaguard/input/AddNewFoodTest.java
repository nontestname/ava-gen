package com.faltenreich.diaguard.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.action.ViewActions.typeText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.hasDescendant;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;
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
public class AddNewFoodTest {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Test
    public void addNewFoodTest() {
        onView(withContentDescription("Open Navigator")).perform(click());
        onView(withId(R.id.nav_food_database)).perform(click());
        onView(allOf(withId(R.id.fab_primary), withContentDescription("New entry")))
                .perform(click());
        onView(allOf(withId(R.id.edit_text), withText("Name")))
                .perform(typeText("mushroom"));
        onView(withId(R.id.fab_primary)).perform(click());

        onView(allOf(withText("Food"), withParent(hasDescendant(withText("CHO per 100 g")))))
                .check(matches(isDisplayed()));
    }

}
