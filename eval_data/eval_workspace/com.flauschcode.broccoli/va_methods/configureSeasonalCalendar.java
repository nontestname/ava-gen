    public void configureSeasonalCalendar() {
        performClick(findNode(withContentDescription("Open navigation drawer")));
        performClick(findNode(withId("nav_settings")));
        performClick(findNode(withId("title"), withText("Region")));
        performClick(findNode(withId("text1"), withText("North America (warmer)")));
        performClick(findNode(withId("title"), withText("Languages of recipes")));
        performClick(findNode(withParentIndex(0), withText("English")));
        performClick(findNode(withText("OK"), withId("button1")));
        performClick(findNode(withContentDescription("Open navigation drawer")));
        performClick(findNode(withId("nav_seasons")));
    }
