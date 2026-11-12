# Implemented Command-Workflow State Diagram

The workflow reads non-comment commands in file order. Settings must precede
`LOAD`; `RUN_APPRAISAL` requires loaded data. A valid appeal must be followed
by a rerun of the affected unit or pool before another appeal or end-of-file.

```mermaid
stateDiagram-v2
    [*] --> ReadingCommands

    ReadingCommands --> ReadingCommands : blank line, comment, or appraisal settings
    ReadingCommands --> DataLoaded : LOAD after required settings
    DataLoaded --> DataLoaded : blank line or comment
    DataLoaded --> AppraisalReady : RUN_APPRAISAL

    AppraisalReady --> AppraisalReady : PRINT_DISTRIBUTION|ALL / append snapshot and write distribution.csv
    AppraisalReady --> AppraisalReady : PRINT_LETTERS|ALL / write letters.csv
    AppraisalReady --> AppraisalReady : invalid APPEAL / reject without applying changes
    AppraisalReady --> AppealPending : valid APPEAL / apply requested manager-rating increases

    AppealPending --> Recalibrating : RERUN_UNIT for the appealed employee's unit or pool
    AppraisalReady --> Recalibrating : RERUN_UNIT without a pending valid appeal
    Recalibrating --> AppraisalReady : recalculate scores, ratings, promotions, and compensation
    Recalibrating --> AppraisalReady : record changed final ratings for the pending appeal

    AppraisalReady --> Finalizing : end of file with LOAD and RUN_APPRAISAL complete
    Finalizing --> ReportsComplete : write appeal_changes.csv
    ReportsComplete --> [*]

    ReadingCommands --> Error : invalid setting, command order, or input
    DataLoaded --> Error : invalid command order or input
    AppraisalReady --> Error : invalid rerun or command
    AppealPending --> Error : end of file before required RERUN_UNIT
```

Each `PRINT_DISTRIBUTION|ALL` appends a numbered snapshot in command order.
`PRINT_LETTERS|ALL` writes the current employee results. A rerun refreshes
compensation after recalibration. Rejected appeals do not mutate ratings.