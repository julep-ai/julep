import { EmitContext, emitFile, resolvePath } from "@typespec/compiler";

export async function $onEmit(context: EmitContext) {
  if (!context.program.compilerOptions.noEmit) {
    await emitFile(context.program, {
      path: resolvePath(context.emitterOutputDir, "output.txt"),
      content: "Hello world\n",
    });
  }
}
