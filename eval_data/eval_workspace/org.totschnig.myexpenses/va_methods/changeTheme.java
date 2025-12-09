    public void changeTheme() {
        performClick(findNode(withContentDescription("More options")));
        performClick(findNode(withText("Settings")));
        performClick(findNode(withText("User interface")));
        performClick(findNode(withText("Theme")));
        performClick(findNode(withText("Light")));
    }
