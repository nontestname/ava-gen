    public void addNewFood() {
        performClick(findNode(withContentDescription("Open Navigator")));
        performClick(findNode(withId("nav_food_database")));
        performClick(findNode(withId("fab_primary"), withContentDescription("New entry")));
        performInput(findNode(withId("edit_text"), withText("Name")), "mushroom");
        performClick(findNode(withId("fab_primary")));
    }
