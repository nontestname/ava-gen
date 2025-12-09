    @Test
    public void addRecipeTest() {
        onView(allOf(withId(R.id.fab_recipes), withContentDescription("New Recipe"),
                isDisplayed())).perform(click());

        onView(allOf(withId(R.id.new_title),
                isDisplayed())).perform(replaceText("Fry Rice"));
        onView(allOf(withId(R.id.new_ingredients),
                isDisplayed())).perform(replaceText("Rice"));
        onView(allOf(withId(R.id.button_save_recipe),
                isDisplayed())).perform(click());


        onView(withText(is("Fry Rice"))).check(matches(isDisplayed()));
        onView(withText(is("Rice"))).check(matches(isDisplayed()));

    }
