    @Test
    public void addCategoryTest() {
        onView(allOf(withContentDescription("Open navigation drawer"),
                isDisplayed())).perform(click());
        onView(allOf(withId(R.id.nav_categories),
                isDisplayed())).perform(click());
        onView(allOf(withId(R.id.fab_categories), withContentDescription("Add category"),
                isDisplayed())).perform(click());
        onView(allOf(withId(R.id.category_name),
                isDisplayed())).perform(replaceText("Lunch"));
        onView(allOf(withId(android.R.id.button1), withText(equalsIgnoreCase("Save"))
        )).perform(click());

        onView(withText(is("Lunch"))).check(matches(isDisplayed()));
    }
