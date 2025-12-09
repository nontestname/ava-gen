    @Test
    public void changeThemeTest() {
        onView(withContentDescription("More options")).perform(click());
        onView(withText("Settings")).perform(click());
        onView(withText("User interface")).perform(click());
        onView(withText("Theme")).perform(click());
        onView(allOf(withText("Light"), isNotChecked())).perform(click());

        onView(allOf(withText("Light"), withParent(hasDescendant(withText("Theme")))))
                .check(matches(isDisplayed()));
    }
