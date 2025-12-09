    @Test
    public void accessArchivePageTest() throws InterruptedException {

        onView(withContentDescription("More options")).perform(click());
        Thread.sleep(1500);
        onView(withText("Archive")).perform(click());
        Thread.sleep(1500);

        onView(withText("Select dates")).check(matches(isDisplayed()));
    }
