let
    Source = Csv.Document(File.Contents(ProjectDataFolder & "\DimCreditLimitGroup.csv"),[Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    // Add a sort order column to ensure logical ordering (Low -> Very High) instead of alphabetical
    AddedSort = Table.AddColumn(PromotedHeaders, "Credit Limit Group Sort", each 
        if [credit_limit_group] = "Low" then 1
        else if [credit_limit_group] = "Medium" then 2
        else if [credit_limit_group] = "High" then 3
        else if [credit_limit_group] = "Very High" then 4
        else 5),
    ChangedType = Table.TransformColumnTypes(AddedSort,{{"credit_limit_group", type text}, {"Credit Limit Group Sort", Int64.Type}})
in
    ChangedType
