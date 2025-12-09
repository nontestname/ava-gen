    @Test
    public void clearEventsTest() throws InterruptedException {

        onView(allOf(withId(R.id.overviewFragment), withContentDescription("Overview"))).perform(click());
        onView(withContentDescription("More options")).perform(click());
        Thread.sleep(1000);
        onView(withText("Event data")).perform(click());
        Thread.sleep(1000);
        onView(withText("Clear events")).perform(click());
        Thread.sleep(1000);
        onView(withText("YES")).perform(click());

        onView(allOf(withClassName(containsStringIgnoringCase("CardView")), withParentIndex(0),
                withParent(withId(R.id.latestReminders)))).check(doesNotExist());

    }
