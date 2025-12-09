    public void addRecipe() {
        performClick(findNode(withId("fab_recipes"), withContentDescription("New Recipe")));
        performInput(findNode(withId("new_title")), "Fry Rice");
        performInput(findNode(withId("new_ingredients")), "Rice");
        performClick(findNode(withId("button_save_recipe")));
    }
