// Tiny static server for e2e tests (no dependencies). Serves build/site; when E2E_FIXTURES=1,
// /data/* is served from e2e/fixture-data so tests never depend on generated data.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, resolve, sep } from "node:path";

const port = Number(process.env.PORT ?? 4173);
const siteRoot = resolve("build/site");
const fixtureRoot = resolve("e2e/fixture-data");
const useFixtures = process.env.E2E_FIXTURES === "1";
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json" };

createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", "http://localhost");
  let path = decodeURIComponent(url.pathname);
  if (path.endsWith("/")) path += "index.html";
  const fromFixture = useFixtures && path.startsWith("/data/");
  const root = fromFixture ? fixtureRoot : siteRoot;
  const rel = fromFixture ? path.slice("/data".length) : path;
  const file = resolve(join(root, normalize(rel)));
  if (file !== root && !file.startsWith(root + sep)) {
    res.writeHead(403).end("forbidden");
    return;
  }
  try {
    const body = await readFile(file);
    res.writeHead(200, { "content-type": types[extname(file)] ?? "application/octet-stream" }).end(body);
  } catch {
    res.writeHead(404).end("not found");
  }
}).listen(port, "127.0.0.1", () => console.log(`serving ${siteRoot} on http://127.0.0.1:${port}`));
