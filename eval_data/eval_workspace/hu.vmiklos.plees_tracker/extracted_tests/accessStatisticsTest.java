    @Test
    public void accessStatisticsTest() throws InterruptedException {
        Thread.sleep(1000);
        onView(withContentDescription("More options")).perform(click());
        onView(allOf(withText("Statistics"), withId(R.id.title))).perform(click());

        onView(withId(R.id.last_week_header)).check(matches(isDisplayed()));
        onView(withId(R.id.last_two_weeks_header)).check(matches(isDisplayed()));
    }
