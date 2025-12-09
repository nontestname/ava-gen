    @Test
    public void deleteAllSleepsTest() throws InterruptedException {
        Thread.sleep(1000);
        onView(withContentDescription("More options")).perform(click());
        onView(withText("Delete All Sleep")).perform(click());
        onView(allOf(withText("YES"), withId(android.R.id.button1))).perform(click());

        onView(withId(R.id.no_sleeps)).check(matches(isDisplayed()));
    }
