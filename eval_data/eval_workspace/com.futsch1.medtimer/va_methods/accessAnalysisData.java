    public void accessAnalysisData() {
        performClick(findNode(withId("statisticsFragment"), withContentDescription("Analysis")));
        performClick(findNode(withId("timeSpinner")));
        performClick(findNode(withText("30 days"), withId("text1"), withParentIndex(5)));
    }
