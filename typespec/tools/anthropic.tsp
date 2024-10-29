import "../common";

using Common;

namespace Tools;


/**
 * Anthropic new tools
 */


model Computer20241022Def {
    type: "computer_20241022" = "computer_20241022";
    name?: string = "computer";

    /** The display width in pixels */
    @minValue(600)
    display_width_px: uint16 = 1024;

    /** The display height in pixels */
    @minValue(400)
    display_height_px: uint16 = 768;

    /** The display number to use */
    @minValue(1)
    @maxValue(10)
    display_number?: uint16 = 1;
}

model TextEditor20241022Def {
    type: "text_editor_20241022" = "text_editor_20241022";
    name?: string = "str_replace_editor";
}

model Bash20241022Def {
    type: "bash_20241022" = "bash_20241022";
    name?: string = "bash";
}

enum Computer20241022Action {
    /** Press a key or key-combination on the keyboard */
    key,

    /** Type a string of text on the keyboard */
    type,

    /** Get the current (x, y) pixel coordinate of the cursor on the screen */
    cursor_position,

    /** Move the cursor to a specified (x, y) pixel coordinate on the screen */
    mouse_move,

    /** Click the left mouse button */
    left_click,

    /** Click the right mouse button */
    right_click,

    /** Click the middle mouse button */
    middle_click,

    /** Double-click the left mouse button */
    double_click,

    /** Take a screenshot of the screen */
    screenshot,
}

model ChosenComputer20241022 {
    /** The action to perform */
    action: Computer20241022Action;

    /** The text to type */
    text?: string;

    /** The (x, y) pixel coordinate to move the cursor to */
    coordinate?: uint16[];
}

model ChosenTextEditor20241022 {
    /** The command to run */
    command: "str_replace" | "insert" | "view" | "undo_edit";

    /** The path to the file */
    path: string;

    /** The content of the file to be created */
    file_text?: string;

    /** The line to insert the new string after */
    insert_line?: uint16;

    /** The new string to insert */
    new_str?: string;

    /** The string in the file to replace */
    old_str?: string;

    /** The line range to view */
    view_range?: uint16[];
}

model ChosenBash20241022 {
    /** The bash command to run */
    command?: string;

    /** Whether to restart the tool */
    restart?: boolean = false;
}
