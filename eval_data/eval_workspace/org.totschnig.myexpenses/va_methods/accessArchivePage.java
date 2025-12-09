    public void accessArchivePage() throws InterruptedException {
        performClick(findNode(withContentDescription("More options")));
        Thread.sleep(1500);
        performClick(findNode(withText("Archive")));
        Thread.sleep(1500);
    }
