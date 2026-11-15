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

    AppraisalReady --> AppraisalReady : RUN_APPRAISAL / recompute when no appeal is pending
    AppraisalReady --> AppraisalReady : PRINT_DISTRIBUTION|ALL / append snapshot and write distribution.csv
    AppraisalReady --> AppraisalReady : PRINT_LETTERS|ALL / write letters.csv
    AppraisalReady --> AppraisalReady : invalid APPEAL / reject without applying changes
    AppraisalReady --> AppealPending : valid APPEAL / apply increases, preserve prior results, mark affected unit

    AppealPending --> AppealPending : RUN_APPRAISAL / reject; retain pre-appeal baseline
    AppealPending --> AppealPending : PRINT_DISTRIBUTION|ALL or PRINT_LETTERS|ALL / write current pre-rerun results
    AppealPending --> Recalibrating : RERUN_UNIT for the appealed employee's unit
    AppealPending --> Error : RERUN_UNIT for a different unit
    AppealPending --> Error : APPEAL before required rerun
    AppraisalReady --> Recalibrating : RERUN_UNIT without a pending valid appeal
    Recalibrating --> AppraisalReady : successful rerun recalculates scores, ratings, promotions and compensation; records all changed ratings and clears pending appeal

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
compensation after recalibration. A pending appeal keeps the last completed
ratings as its comparison baseline; `RUN_APPRAISAL` is rejected until
`RERUN_UNIT` is run for the affected unit. The pending appeal is cleared only
after the rerun and compensation refresh succeed. Rejected appeals do not
mutate ratings.