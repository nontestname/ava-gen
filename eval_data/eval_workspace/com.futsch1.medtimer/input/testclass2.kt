package com.futsch1.medtimer.test2va

import android.view.View
import android.view.ViewGroup
import android.view.ViewParent

import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.action.ViewActions.closeSoftKeyboard
import androidx.test.espresso.action.ViewActions.replaceText
import androidx.test.espresso.action.ViewActions.scrollTo
import androidx.test.espresso.action.ViewActions.typeText
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.isDisplayed
import androidx.test.espresso.matcher.ViewMatchers.withClassName
import androidx.test.espresso.matcher.ViewMatchers.withContentDescription
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withParent
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.espresso.matcher.ViewMatchers
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.LargeTest
import androidx.test.rule.GrantPermissionRule

import com.futsch1.medtimer.MainActivity
import com.futsch1.medtimer.R

import org.hamcrest.Matchers.allOf
import org.hamcrest.Matchers.containsStringIgnoringCase
import org.hamcrest.Matchers.`is`
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@LargeTest
@RunWith(AndroidJUnit4::class)
class TestClass1 {

    @get:Rule
    val activityScenarioRule = ActivityScenarioRule(MainActivity::class.java)

    @get:Rule
    val grantPermissionRule: GrantPermissionRule =
        GrantPermissionRule.grant("android.permission.POST_NOTIFICATIONS")

    @Test
    fun addNewMedicineTest2() {

        onView(
            allOf(
                ViewMatchers.withId(R.id.medicinesFragment),
                withContentDescription("Medicine")
            )
        ).perform(click())

        onView(allOf(withId(R.id.addMedicine), withText("Add medicine")))
            .perform(click())

        onView(withClassName(containsStringIgnoringCase("EditText")))
            .perform(typeText("Claritin"))

        onView(allOf(withId(android.R.id.button1), withText("OK")))
            .perform(click())

        onView(allOf(withId(R.id.medicineName), withText("Claritin")))
            .check(matches(isDisplayed()))
    }

    @Test
    fun updateOverviewDisplayEventsTest2() {

        onView(
            allOf(
                withId(R.id.overviewFragment),
                withContentDescription("Overview")
            )
        ).perform(click())

        onView(withContentDescription("More options"))
            .perform(click())

        onView(withText("Settings"))
            .perform(click())

        onView(
            allOf(
                withText("Overview display events"),
                withId(android.R.id.title)
            )
        ).perform(click())

        onView(
            allOf(
                withText("7 days"),
                withId(android.R.id.text1),
                withClassName(containsStringIgnoringCase("CheckedTextView"))
            )
        ).perform(click())

        onView(
            allOf(
                withId(android.R.id.summary),
                withText("7 days"),
                withParent(
                    ViewMatchers.hasDescendant(
                        withText("Overview display events")
                    )
                )
            )
        ).check(matches(isDisplayed()))
    }
}