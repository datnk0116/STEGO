# Submission outputs

The previous binary files were generated from an older report revision and have been removed to prevent accidental submission of stale files.

Build fresh files from the current checkout:

~~~bash
python scripts/build_submission.py
~~~

The command creates:
- STUDENT_UETCN3124_CTF_Report.docx
- STUDENT_UETCN3124_CTF_Report.pdf
- STUDENT_UETCN3124_Scripts.zip

The build stops if the main report body exceeds 15 pages. Review the PDF visually and fill in student identity and personal reflection before submitting. Commit generated binaries only after confirming that they were built from the same source revision.
