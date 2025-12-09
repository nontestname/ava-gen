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
