    public void deleteAllSleeps() throws InterruptedException {
        Thread.sleep(1000);
        performClick(findNode(withContentDescription("More options")));
        performClick(findNode(withText("Delete All Sleep")));
        performClick(findNode(withText("YES"), withId("button1")));
    }
