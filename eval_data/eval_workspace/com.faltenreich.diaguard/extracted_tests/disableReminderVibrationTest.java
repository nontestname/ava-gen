    @Test
    public void disableReminderVibrationTest() {
        onView(withContentDescription("Open Navigator")).perform(click());
        onView(withId(R.id.nav_settings)).perform(click());
        onView(withText("Vibration")).perform(click());


        onView(allOf(withId(android.R.id.checkbox),withParent(withParent(hasDescendant(withText("Vibration"))))))
                .check(matches(isNotChecked()));

    }
