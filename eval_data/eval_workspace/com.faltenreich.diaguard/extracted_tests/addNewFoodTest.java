    @Test
    public void addNewFoodTest() {
        onView(withContentDescription("Open Navigator")).perform(click());
        onView(withId(R.id.nav_food_database)).perform(click());
        onView(allOf(withId(R.id.fab_primary), withContentDescription("New entry")))
                .perform(click());
        onView(allOf(withId(R.id.edit_text), withText("Name")))
                .perform(typeText("mushroom"));
        onView(withId(R.id.fab_primary)).perform(click());

        onView(allOf(withText("Food"), withParent(hasDescendant(withText("CHO per 100 g")))))
                .check(matches(isDisplayed()));
    }
