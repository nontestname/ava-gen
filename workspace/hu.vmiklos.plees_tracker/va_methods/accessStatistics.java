    public void accessStatistics() throws InterruptedException {
        Thread.sleep(1000);
        performClick(findNode(withContentDescription("More options")));
        performClick(findNode(withText("Statistics"), withId("title")));
    }
