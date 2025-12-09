    public void startSleep() throws InterruptedException {
        Thread.sleep(2000);
        performClick(findNode(withId("start_stop_text"), withText("Start")));
        Thread.sleep(2000);
    }
