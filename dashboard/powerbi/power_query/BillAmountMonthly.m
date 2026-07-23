let
    // Reference the FactCreditCustomer query directly to preserve its base grain untouched
    Source = FactCreditCustomer,
    // Select only the columns needed for monthly bill trends
    SelectedColumns = Table.SelectColumns(Source,{"id", "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"}),
    // Unpivot to create a long format (one row per customer per month)
    UnpivotedColumns = Table.UnpivotOtherColumns(SelectedColumns, {"id"}, "Bill Month", "Bill Amount"),
    // Extract the final digit from the attribute to determine the Month Number
    AddedMonthNumber = Table.AddColumn(UnpivotedColumns, "Month Number", each Number.From(Text.End([Bill Month], 1))),
    // Ensure Month Number is treated as an integer for correct chronological sorting
    ChangedType = Table.TransformColumnTypes(AddedMonthNumber,{{"Month Number", Int64.Type}, {"Bill Amount", type number}})
in
    ChangedType
