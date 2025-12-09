    public void changeWeightUnit() {
        performClick(findNode(withContentDescription("Open Navigator")));
        performClick(findNode(withId("nav_settings")));
        performScrollDown();
        performClick(findNode(withText("Units")));
        performClick(findNode(withText("Weight")));
        performClick(findNode(withText("Pound")));
    }
