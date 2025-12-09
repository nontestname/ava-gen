    @Test
    public void accessSupportPageTest() {
        onView(allOf(withContentDescription("Open navigation drawer"),
                isDisplayed())).perform(click());
        onView(allOf(withId(R.id.nav_support),
                isDisplayed())).perform(click());

        onView(allOf(withId(R.id.buy_me_coffee_button))).check(matches(isDisplayed()));
    }
