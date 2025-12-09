    @Test
    fun addNewMedicineTest2() {

        onView(
            allOf(
                ViewMatchers.withId(R.id.medicinesFragment),
                withContentDescription("Medicine")
            )
        ).perform(click())

        onView(allOf(withId(R.id.addMedicine), withText("Add medicine")))
            .perform(click())

        onView(withClassName(containsStringIgnoringCase("EditText")))
            .perform(typeText("Claritin"))

        onView(allOf(withId(android.R.id.button1), withText("OK")))
            .perform(click())

        onView(allOf(withId(R.id.medicineName), withText("Claritin")))
            .check(matches(isDisplayed()))
    }
