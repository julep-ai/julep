from fire import Fire
from transformers import AutoTokenizer


def update_tokenizer_template(
    tokenizer_name: str = "julep-ai/samantha-1-turbo",
    template_path: str = "./model_api/chat_template.jinja",
    save_to_dir: str | None = None,
    push_to_hub: bool = False,
):
    assert (
        save_to_dir is not None or push_to_hub
    ), "You must specify a directory to save the tokenizer to or push to the Hugging Face model hub."

    # Load the tokenizer
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    # Set the template
    with open(template_path, "r") as f:
        template = f.read()

    tokenizer.chat_template = template

    # Save the tokenizer
    if save_to_dir:
        tokenizer.save_pretrained(save_to_dir)

    # Push to the Hugging Face model hub
    if push_to_hub:
        tokenizer.push_to_hub(tokenizer_name)


if __name__ == "__main__":
    Fire(update_tokenizer_template)
