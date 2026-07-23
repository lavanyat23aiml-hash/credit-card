let
    // Uses the ProjectDataFolder text parameter so no hardcoded local paths exist
    Source = Csv.Document(File.Contents(ProjectDataFolder & "\FactCreditCustomer.csv"),[Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    // Ensure id is a whole number for reliable joining
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{
        {"id", Int64.Type},
        {"limit_bal", type number},
        {"age", Int64.Type},
        {"sex", Int64.Type},
        {"education", Int64.Type},
        {"marriage", Int64.Type},
        {"default_payment_next_month", Int64.Type}
    })
in
    ChangedType
