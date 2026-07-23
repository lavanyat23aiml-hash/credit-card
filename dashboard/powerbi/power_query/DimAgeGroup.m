let
    Source = Csv.Document(File.Contents(ProjectDataFolder & "\DimAgeGroup.csv"),[Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    // Add a sort order column so "20-29" appears before "30-39" etc. instead of alphabetical sorting if anomalies exist
    AddedSort = Table.AddColumn(PromotedHeaders, "Age Group Sort", each 
        if Text.StartsWith([age_group], "2") then 1
        else if Text.StartsWith([age_group], "3") then 2
        else if Text.StartsWith([age_group], "4") then 3
        else if Text.StartsWith([age_group], "5") then 4
        else if Text.StartsWith([age_group], "6") then 5
        else 6),
    ChangedType = Table.TransformColumnTypes(AddedSort,{{"age_group", type text}, {"Age Group Sort", Int64.Type}})
in
    ChangedType
