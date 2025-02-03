# Define a recursive walk function that applies f to every value.
def walk(f):
  . as $in
  | if type == "object" then
      reduce keys[] as $key ({}; . + { ($key): ($in[$key] | walk(f)) })
    elif type == "array" then
      map( walk(f) )
    else
      .
    end
  | f;

# Save the whole document as $root so we can look up definitions.
. as $root
| walk(
    if type=="object" and has("$ref")
    then
      # Look up the key (the last component of the ref)
      $root.components.schemas[(.["$ref"] | split("/") | last)]
    else
      .
    end
)

