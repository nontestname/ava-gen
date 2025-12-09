# supported_espresso_apis.py

# Define the set of supported non-Espresso method names
SUPPORTED_NON_ESPRESSO = {
    "closeSoftKeyboard()",
    "closeSoftKeyboard();",
    "pressBack()",
    "pressBack();"

}


IGNORED_MATCHERS = {

    "isDisplayed",
    "isNotChecked",
    "isChecked",
    "isEnabled",
    "isNotEnabled",
    
    "containsString"
}

# Example lists of supported matchers and actions from espresso APIs
SUPPORTED_MATCHERS = {
    "onView",
    "allOf",
    "withId",
    "withText",
    "withContentDescription",
    "withClassName",
    "withParent",
    "withParentIndex",
    "hasDescendant",

    "isRoot",
    "containsStringIgnoringCase",
}

# Append ignored matchers so validator will accept them
SUPPORTED_MATCHERS |= IGNORED_MATCHERS

SUPPORTED_ACTIONS = {
    "click",
    "swipeLeft",
    "swipeRight",
    "replaceText",
    "typeText",
    "longClick",
    "scrollTo"
}

