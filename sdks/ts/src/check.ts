import typia, { tags } from "typia";

export const check = typia.createIs<IMember>();

interface IMember {
  id: string & tags.Format<"uuid">;
  email: string & tags.Format<"email">;
  age: number & tags.ExclusiveMinimum<19> & tags.Maximum<100>;
}
