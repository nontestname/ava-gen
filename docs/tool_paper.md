# Tool Paper & Evaluation Artifacts

This page summarizes the research tool paper associated with AVA‑Gen and
points to the evaluation data and reports stored in this repository.

## Paper information

**Title**  
AVA-Gen: An Automated Voice Assistant Generation Framework from GUI Test Cases Reusing

**Abstract**  
Voice assistants (VAs) are increasingly used on mobile devices, yet integrating VA capabilities into existing applications remains labor-intensive and difficult to scale. We present AVA-Gen, an automated framework that generates voice-assistant functionality directly from an app’s GUI test code. AVA-Gen first builds a static analysis pipeline to convert the test methods to VA-ready artifacts, such as VA methods, task intents, skill descriptions, and executable action plans. At runtime, AVA-Gen provides a server–client architecture that validates user intents and executes the generated action plans on an Android device. Our evaluation shows that AVA-Gen successfully converts 19 out of 20 test methods to VA methods from five applications, and correctly handles 88 of 100 simulated user queries with different accuracy levels.

---

## Evaluation data

All evaluation data used in the paper is stored under the `eval_data/`
directory in this repository.

### 1. Evaluation workspaces

All the five tested application apks (install files) and their generated artifacts are in the :

```text
eval_data/eval_workspace/
  actionplan/
  intent/
  skills_description/
  com.faltenreich.diaguard/
  com.flauschcode.broccoli/
  com.futsch1.medtimer/
  hu.vmiklos.plees_tracker/
  org.totschnig.myexpenses/
eval_data/apks/
```

### 2. Evaluation reports

Path:

```text
eval_data/eval_report/
```

This folder is reserved for evaluation summaries, metrics, and any post‑processing scripts or CSVs used in the paper’s analysis.
