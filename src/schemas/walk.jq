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
| .components.schemas[$target] + {"$defs": $root.components.schemas}
| walk(
    if type=="string" and startswith("#/components/schema")
    then
      . | sub("components/schemas"; "$defs")
    else
      .
    end
)

