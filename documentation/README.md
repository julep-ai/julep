```markdown
# Julep Mintlify Documentation

## Development

Install the [Mintlify CLI](https://www.npmjs.com/package/mintlify) to preview the documentation changes locally. To install, use the following command:

```
npm i -g mintlify
```

Run the following command at the root of your documentation (where mint.json is):

```
mintlify dev
```

### Troubleshooting

- Mintlify dev isn't running - Run `mintlify install` it'll re-install dependencies.
- Page loads as a 404 - Make sure you are running in a folder with `mint.json`

## Integration of Entelligence Chat

The `entelligence-chat.js` script has been added to enhance the Julep documentation with a chat widget. This script integrates a chat interface that allows users to interact with Julep AI directly from the documentation.

### Purpose

The `entelligence-chat.js` script is designed to:

- Inject a chat widget into the documentation using a shadow DOM for style encapsulation.
- Load necessary styles and scripts from a CDN to ensure the chat widget is styled and functions correctly.
- Initialize the chat widget with specific analytics data, including repository and organization details, API key, theme, and company name.

### How It Works

1. **Script Initialization**: The script checks if the `entelligence-chat` script is already present. If not, it creates and appends the script to the document head.

2. **Loading Styles**: Once the chat script is loaded, it fetches the required CSS from a CDN and applies it to both the shadow DOM and the document head to ensure consistent styling.

3. **Widget Initialization**: The chat widget is initialized with configuration data, including analytics and theme settings.

4. **Event Handling**: The script ensures that the chat widget is initialized once the document is fully loaded, using the `DOMContentLoaded` event.

### Usage

To integrate the Entelligence Chat into your documentation:

- Ensure the `entelligence-chat.js` script is included in your documentation's scripts directory.
- The script will automatically initialize when the documentation page is loaded, provided the necessary HTML element with the ID `entelligence-chat-root` is present in the document.

By following these steps, you can provide users with an interactive chat experience directly within your documentation, enhancing user engagement and support.
```