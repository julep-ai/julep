import "../common";

using Common;

namespace Tools;

/** Arguments for Ffmpeg CMD */
model FfmpegSearchArguments {
    /** The bash command string */
    cmd: string;

     /** The base64 string of the file*/
    file?: string;

}

/** Ffmpeg integration definition */
model FfmpegIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "ffmpeg" */
    provider: "ffmpeg" = "ffmpeg";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Ffmpeg */
    setup?: null = null;
    
    /** The arguments for Ffmpeg Search */
    arguments?: FfmpegSearchArguments;
}

/** Ffmpeg Provider Card */
model FfmpegProviderCard extends BaseProviderCard {
    provider: "ffmpeg" = "ffmpeg";
    setup: null = null;
    methods: ProviderMethod<FfmpegSearchArguments, FfmpegSearchOutput>[] = #[
        #{
            method: "bash_cmd",
            description: "Run FFmpeg bash command",
        }
    ];
    info: ProviderInfo = #{
        url: "https://ffmpeg.org/",
        docs: "https://ffmpeg.org/documentation.html",
        icon: "https://upload.wikimedia.org/wikipedia/commons/5/5f/FFmpeg_Logo_new.svg",
        friendly_name: "Ffmpeg",
    };
}

/** Ffmpeg Search Output */
model FfmpegSearchOutput {
    /** The documents returned from the Ffmpeg search */
    file: string;
    result: boolean;
    mime_type: string;
}