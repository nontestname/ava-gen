    @Test
    public void changeWeightUnitTest() {

        onView(withContentDescription("Open Navigator")).perform(click());
        onView(withId(R.id.nav_settings)).perform(click());

        onView(allOf(withText("Units"))).perform(scrollTo());
        onView(withText("Units")).perform(click());
        onView(withText("Weight")).perform(click());

        onView(allOf(withText("Pound")))
                .perform(click());

        onView(allOf(withId(android.R.id.summary), withText("Pound"),
                        withParent(hasDescendant(withText("Weight")))))
                .check(matches(isDisplayed()));

    }
