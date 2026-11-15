import { cpSync, mkdirSync } from "node:fs";
mkdirSync("build/site", { recursive: true });
cpSync("static", "build/site", { recursive: true });
cpSync("build/js", "build/site/js", { recursive: true });
