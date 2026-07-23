let
    // Reference the FactCreditCustomer query directly to preserve its base grain untouched
    Source = FactCreditCustomer,
    // Select only the columns needed for monthly payment trends
    SelectedColumns = Table.SelectColumns(Source,{"id", "pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"}),
    // Unpivot to create a long format (one row per customer per month)
    UnpivotedColumns = Table.UnpivotOtherColumns(SelectedColumns, {"id"}, "Pay Month", "Pay Amount"),
    // Extract the final digit from the attribute to determine the Month Number
    AddedMonthNumber = Table.AddColumn(UnpivotedColumns, "Month Number", each Number.From(Text.End([Pay Month], 1))),
    // Ensure Month Number is treated as an integer for correct chronological sorting
    ChangedType = Table.TransformColumnTypes(AddedMonthNumber,{{"Month Number", Int64.Type}, {"Pay Amount", type number}})
in
    ChangedType
