import "../common";

using Common;

namespace Tools;

/** Integration definition for Weather */
model WeatherSetup {
    /** The api key for OpenWeatherMap */
    openweathermap_api_key: string;
}

/** Arguments for Weather */
model WeatherGetArguments {
    /** The location for which to fetch weather data */
    location: string;
}

/** Weather integration definition */
model WeatherIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "weather" */
    provider: "weather" = "weather";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Weather */
    setup?: WeatherSetup;
    
    /** The arguments for Weather */
    arguments?: WeatherGetArguments;
} 