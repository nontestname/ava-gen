    public void updateOverviewDisplayEvents() {
        performClick(findNode(withId("overviewFragment"), withContentDescription("Overview")));
        performClick(findNode(withContentDescription("More options")));
        performClick(findNode(withText("Settings")));
        performClick(findNode(withText("Overview display events"), withId("title")));
        performClick(findNode(withText("7 days"), withId("text1")));
    }
