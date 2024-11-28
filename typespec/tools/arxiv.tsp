import "../common";

using Common;

namespace Tools;

/** Arguments for Arxiv Search */
model ArxivSearchArguments {
    /** The search query for searching with Arxiv */
    query: string;

    /** The list of Arxiv IDs to search with */
    id_list?: Array<string>;

    /** The maximum number of results to return */
    @minValue(1)
    @maxValue(300000)
    max_results?: int16 = 10;

    /** The download the pdf of the results */
    download_pdf?: boolean = false;

    /** The sort criterion for the results */
    sort_by?: "relevance" | "lastUpdatedDate" | "submittedDate" = "relevance";

    /** The sort order for the results */
    sort_order?: "ascending" | "descending" = "descending";
}

/** Arxiv integration definition */
model ArxivIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "arxiv" */
    provider: "arxiv" = "arxiv";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Arxiv */
    setup?: null = null;
    
    /** The arguments for Arxiv Search */
    arguments?: ArxivSearchArguments;
} 

/** The result of the Arxiv Search */
model ArxivSearchOutput {
    result: string;
}

model ArxivProviderCard extends BaseProviderCard {
    provider: "arxiv" = "arxiv";
    setup: null = null;
    methods: ProviderMethod<ArxivSearchArguments, ArxivSearchOutput>[] = #[
        #{
            method: "search",
            description: "Search with Arxiv",
        }
    ];
    info: ProviderInfo = #{
        url: "https://pypi.org/project/arxiv/",
        docs: "https://info.arxiv.org/help/api/index.html",
        icon: "https://arxiv.com/favicon.ico",
        friendly_name: "Arxiv Search",
    };
}