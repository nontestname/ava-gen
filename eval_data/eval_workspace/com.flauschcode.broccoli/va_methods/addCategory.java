    public void addCategory() {
        performClick(findNode(withContentDescription("Open navigation drawer")));
        performClick(findNode(withId("nav_categories")));
        performClick(findNode(withId("fab_categories"), withContentDescription("Add category")));
        performInput(findNode(withId("category_name")), "Lunch");
        performClick(findNode(withId("button1"), withText(equalsIgnoreCase("Save"))));
    }
