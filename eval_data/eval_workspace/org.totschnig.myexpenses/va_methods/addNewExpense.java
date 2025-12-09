    public void addNewExpense() throws InterruptedException {
        performClick(findNode(withId("fab")));
        Thread.sleep(1000);
        performInput(findNode(withId("AmountEditText"), withParent(withId("Amount"), hasDescendant(withId("TaType")))), "20");
        performClick(findNode(withId("fab")));
    }
