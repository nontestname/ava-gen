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
