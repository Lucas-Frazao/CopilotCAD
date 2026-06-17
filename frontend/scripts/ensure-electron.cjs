const { downloadArtifact } = require("@electron/get");
const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const electronDir = path.join(__dirname, "..", "node_modules", "electron");
const { version } = require(path.join(electronDir, "package.json"));
const checksums = require(path.join(electronDir, "checksums.json"));

const platformPath =
  process.platform === "win32"
    ? "electron.exe"
    : process.platform === "darwin"
      ? "Electron.app/Contents/MacOS/Electron"
      : "electron";

const distPath = path.join(electronDir, "dist");
const electronBinary = path.join(distPath, platformPath);

function extractZip(zipPath, destination) {
  if (process.platform === "win32") {
    execFileSync(
      "powershell",
      [
        "-NoProfile",
        "-Command",
        `Expand-Archive -LiteralPath '${zipPath.replace(/'/g, "''")}' -DestinationPath '${destination.replace(/'/g, "''")}' -Force`,
      ],
      { stdio: "inherit" },
    );
    return;
  }

  execFileSync("tar", ["-xf", zipPath, "-C", destination], { stdio: "inherit" });
}

async function main() {
  if (fs.existsSync(electronBinary)) {
    return;
  }

  const zipPath = await downloadArtifact({
    version,
    artifactName: "electron",
    platform: process.platform,
    arch: process.arch,
    checksums,
  });

  fs.rmSync(distPath, { recursive: true, force: true });
  fs.mkdirSync(distPath, { recursive: true });
  extractZip(zipPath, distPath);
  await fs.promises.writeFile(path.join(electronDir, "path.txt"), platformPath);
  console.log("Electron binary installed.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
