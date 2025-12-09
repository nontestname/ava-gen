    public void addNewMedicine() {
        performClick(findNode(withId("medicinesFragment"), withContentDescription("Medicine")));
        performClick(findNode(withId("addMedicine"), withText("Add medicine")));
        performInput(findNode(withClassName(containsStringIgnoringCase("EditText"))), "Claritin");
        performClick(findNode(withId("button1"), withText("OK")));
    }
