import "../../common";

using Common;

namespace Tools;


/** browserbase extension provider */
model BrowserbaseExtensionIntegrationDef extends BaseBrowserbaseIntegrationDef {
    /** The specific method of the integration to call */
    method?: "install_extension_from_github";

    /** The arguments for the method */
    arguments?: BrowserbaseExtensionArguments;
}

model BrowserbaseExtensionArguments {
    /** The GitHub repository name. */
    repositoryName: string;

    /** Ref to install from a branch or tag. */
    ref?: string;
}

model BrowserbaseExtensionOutput {
    /** The installed Extension ID. */
    id: string;
}
