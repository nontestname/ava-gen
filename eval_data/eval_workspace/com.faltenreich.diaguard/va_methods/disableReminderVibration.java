    public void disableReminderVibration() {
        performClick(findNode(withContentDescription("Open Navigator")));
        performClick(findNode(withId("nav_settings")));
        performClick(findNode(withText("Vibration")));
    }
