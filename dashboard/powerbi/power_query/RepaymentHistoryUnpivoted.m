let
    // Reference the FactCreditCustomer query directly
    Source = FactCreditCustomer,
    // Select only the repayment status columns (note: original dataset has no pay_1)
    SelectedColumns = Table.SelectColumns(Source,{"id", "pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"}),
    // Unpivot to create a long format so it can be joined to DimRepaymentStatus
    UnpivotedColumns = Table.UnpivotOtherColumns(SelectedColumns, {"id"}, "Repayment Period", "Repayment Status"),
    // Ensure Repayment Status is an integer to match DimRepaymentStatus
    ChangedType = Table.TransformColumnTypes(UnpivotedColumns,{{"Repayment Status", Int64.Type}})
in
    ChangedType
