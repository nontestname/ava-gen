package com.flauschcode.broccoli.test2va;


import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.action.ViewActions.replaceText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.hasDescendant;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withContentDescription;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withParent;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.is;

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
public class AddRecipeTest {

    @Rule
    public ActivityScenarioRule<MainActivity> mActivityScenarioRule =
            new ActivityScenarioRule<>(MainActivity.class);

    @Test
    public void addRecipeTest() {
        onView(allOf(withId(R.id.fab_recipes), withContentDescription("New Recipe"),
                isDisplayed())).perform(click());

        onView(allOf(withId(R.id.new_title),
                isDisplayed())).perform(replaceText("Fry Rice"));
        onView(allOf(withId(R.id.new_ingredients),
                isDisplayed())).perform(replaceText("Rice"));
        onView(allOf(withId(R.id.button_save_recipe),
                isDisplayed())).perform(click());


        onView(withText(is("Fry Rice"))).check(matches(isDisplayed()));
        onView(withText(is("Rice"))).check(matches(isDisplayed()));

    }
    
}
