    @Test
    public void startSleepTest() throws InterruptedException {
        Thread.sleep(2000);
        onView(allOf(withId(R.id.start_stop_text), withText("Start"))).perform(click());
        Thread.sleep(2000);
        onView(allOf(withId(R.id.start_stop_text), withText("Stop"))).check(matches(isDisplayed()));
    }
