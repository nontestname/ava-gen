    @Test
    public void updateReportDurationTest() {

        onView(withContentDescription("More options")).perform(click());
        onView(allOf(withText("Settings"), withId(R.id.title))).perform(click());
        onView(allOf(withText("Duration"), withId(android.R.id.title))).perform(click());
        onView(withText("Last month")).perform(click());

        onView(allOf(withText("Last month"), withParent(hasDescendant(withText("Duration")))))
                .check(matches(isDisplayed()));
    }
