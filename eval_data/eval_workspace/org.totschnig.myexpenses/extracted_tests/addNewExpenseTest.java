    @Test
    public void addNewExpenseTest() throws InterruptedException {
        onView(allOf(withId(R.id.fab),
                isDisplayed())).perform(click());
        Thread.sleep(1000);
        onView(allOf(withId(R.id.AmountEditText), withParent(allOf(withId(R.id.Amount),
                hasDescendant(allOf(withId(R.id.TaType), isNotChecked())))))).perform(replaceText("20"));
        onView(allOf(withId(R.id.fab), isDisplayed())).perform(click());

        onView(withText(containsString("20"))).check(matches(isDisplayed()));
    }
