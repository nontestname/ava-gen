    public void updateReportDuration() {
        performClick(findNode(withContentDescription("More options")));
        performClick(findNode(withText("Settings"), withId("title")));
        performClick(findNode(withText("Duration"), withId("title")));
        performClick(findNode(withText("Last month")));
    }
