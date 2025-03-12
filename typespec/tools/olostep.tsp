import "./models.tsp";

@doc("Olostep setup configuration")
model OlostepSetup {
  @doc("Olostep API key")
  olostep_api_key: string;
}

@doc("Parameters for scraping request")
model OlostepScrapeArguments {
  @doc("URL to scrape")
  url: string;

  @doc("Additional parameters for scraping")
  params?: {
    @doc("Time to wait before scraping (ms)")
    wait_before_scraping?: int32;

    @doc("Content formats to return")
    formats?: string[];

    @doc("CSS selectors removal configuration")
    remove_css_selectors?: "default" | "none" | "array";

    @doc("Actions to perform before scraping")
    actions?: OlostepAction[];

    @doc("Country to route request through")
    country?: string;

    @doc("Content transformer")
    transformer?: "postlight" | "none";

    @doc("Remove images from content")
    remove_images?: boolean;

    @doc("Class names to remove")
    remove_class_names?: string[];

    @doc("Screen size configuration")
    screen_size?: {
      screen_type?: "desktop" | "mobile" | "default";
      screen_width?: int32;
      screen_height?: int32;
    };

    @doc("Link extraction configuration")
    links_on_page?: {
      absolute_links?: boolean;
      query_to_order_links_by?: string;
    };
  };
}

@doc("Action to perform on page")
model OlostepAction {
  @doc("Action type")
  type: "wait" | "click" | "fill" | "scroll";
  
  @doc("Action parameters")
  params?: Record<string>;
}

@doc("Olostep response format")
model OlostepResponse {
  @doc("URL that was scraped")
  url: string;

  @doc("Scraped content")
  content: string;

  @doc("Error message if failed")
  error?: string;

  @doc("Scrape status")
  status: string;
}

@doc("Output from Olostep operation")
model OlostepOutput {
  @doc("Array of scraping results")
  result: OlostepResponse[];
}