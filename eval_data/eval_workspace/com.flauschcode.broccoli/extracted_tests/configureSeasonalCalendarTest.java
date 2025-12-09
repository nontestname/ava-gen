    @Test
    public void configureSeasonalCalendarTest() {
        onView(withContentDescription("Open navigation drawer")).perform(click());
        onView(withId(R.id.nav_settings)).perform(click());

        // set region
        onView(allOf(withId(android.R.id.title), withText("Region")))
                .perform(click());
        onView(allOf(withId(android.R.id.text1), withText("North America (warmer)"))).perform(click());

        // language
        onView(allOf(withId(android.R.id.title), withText("Languages of recipes")))
                .perform(click());
        onView(allOf(withParentIndex(0), withText("English"))).perform(click());
        onView(allOf(withText("OK"), withId(android.R.id.button1))).perform(click());


        onView(withContentDescription("Open navigation drawer")).perform(click());
        onView(withId(R.id.nav_seasons)).perform(click());

        onView(allOf(withId(R.id.seasons_configure), withText("CONFIGURE")))
                .check(doesNotExist());

    }
