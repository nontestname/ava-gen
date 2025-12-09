    public void accessStatistics() {
        performClick(findNode(withContentDescription("Open Navigator")));
        performClick(findNode(withId("nav_statistics")));
        performClick(findNode(withId("category_spinner")));
        performClick(findNode(withId("text1"), withText("Weight")));
        performClick(findNode(withId("interval_spinner")));
        performClick(findNode(withId("text1"), withText("Month")));
    }
