    public void clearEvents() throws InterruptedException {
        performClick(findNode(withId("overviewFragment"), withContentDescription("Overview")));
        performClick(findNode(withContentDescription("More options")));
        Thread.sleep(1000);
        performClick(findNode(withText("Event data")));
        Thread.sleep(1000);
        performClick(findNode(withText("Clear events")));
        Thread.sleep(1000);
        performClick(findNode(withText("YES")));
    }
