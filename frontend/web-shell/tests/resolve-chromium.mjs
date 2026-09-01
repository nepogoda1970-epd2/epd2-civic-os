import {
  chmodSync,
  createReadStream,
  createWriteStream,
  existsSync,
  mkdirSync,
  writeFileSync,
} from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { pipeline } from "node:stream/promises";
import { fileURLToPath } from "node:url";
import { createBrotliDecompress } from "node:zlib";

const here = dirname(fileURLToPath(import.meta.url));
const sourceDir = join(here, "../../../node_modules/@sparticuz/chromium/bin");
const runtimeDir = process.env.TMPDIR ?? "/tmp";
const chromiumPath = join(runtimeDir, "chromium");

mkdirSync(runtimeDir, { recursive: true });

async function inflateFile(sourceName, target) {
  if (existsSync(target)) return;
  await pipeline(
    createReadStream(join(sourceDir, sourceName)),
    createBrotliDecompress(),
    createWriteStream(target, { mode: 0o700 }),
  );
}

async function inflateTar(sourceName, targetDir) {
  const marker = join(targetDir, ".complete");
  if (existsSync(marker)) return;
  mkdirSync(targetDir, { recursive: true });
  const archive = join(runtimeDir, `${sourceName}.tar`);
  await pipeline(
    createReadStream(join(sourceDir, sourceName)),
    createBrotliDecompress(),
    createWriteStream(archive),
  );
  // --no-same-owner is required on restricted/overlay filesystems.
  execFileSync("tar", [
    "--extract",
    "--file",
    archive,
    "--directory",
    targetDir,
    "--no-same-owner",
    "--no-same-permissions",
  ]);
  createWriteStream(marker).end();
}

await inflateFile("chromium.br", chromiumPath);
await Promise.all([
  inflateTar("fonts.tar.br", join(runtimeDir, "fonts")),
  inflateTar("swiftshader.tar.br", runtimeDir),
  inflateTar("al2023.tar.br", join(runtimeDir, "al2023")),
]);
writeFileSync(
  join(runtimeDir, "fonts", "fonts.conf"),
  `<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>${join(runtimeDir, "fonts", "fonts")}</dir>
  <cachedir>${join(runtimeDir, "cache", "fontconfig")}</cachedir>
  <config></config>
</fontconfig>
`,
);
chmodSync(chromiumPath, 0o700);
process.stdout.write(chromiumPath);
