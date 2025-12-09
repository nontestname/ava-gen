    @Test
    public void switchingAccountTest() {

        onView(isRoot()).perform(swipeLeft());

        onView(withText("Saving Account")).check(matches(isDisplayed()));
    }
