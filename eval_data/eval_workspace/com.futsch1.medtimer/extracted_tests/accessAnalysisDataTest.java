    @Test
    public void accessAnalysisDataTest() {
        onView(allOf(withId(R.id.statisticsFragment),
                withContentDescription("Analysis"))).perform(click());
        onView(withId(R.id.timeSpinner)).perform(click());
        onView(allOf(withText("30 days"), withId(android.R.id.text1), withParentIndex(5)))
                .perform(click());

        onView(allOf(withId(R.id.timeSpinner), hasDescendant(withText("30 days"))))
                .check(matches(isDisplayed()));

    }
