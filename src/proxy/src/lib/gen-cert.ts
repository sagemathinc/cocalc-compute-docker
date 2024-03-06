/* Generate a self-signed cert.  The genCert function returns an object
 {key, cert} suitable to give as input to the https createServer function.
*/

import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { join } from "path";
import { tmpdir } from "node:os";

export default async function genCert() {
  const tmpDir = await mkdtemp(join(tmpdir(), "cert-"));
  try {
    const keyFile = join(tmpDir, "key.pem");
    const certFile = join(tmpDir, "cert.pem");
    await genCertFiles({ keyFile, certFile });
    const key = (await readFile(keyFile)).toString();
    const cert = (await readFile(certFile)).toString();
    return { key, cert };
  } finally {
    await rm(tmpDir, { recursive: true });
  }
}

async function genCertFiles({
  keyFile,
  certFile,
}: {
  keyFile: string;
  certFile: string;
}): Promise<void> {
  return new Promise((resolve, reject) => {
    const openssl = spawn("openssl", [
      "req",
      "-new",
      "-x509",
      "-nodes",
      "-out",
      certFile,
      "-keyout",
      keyFile,
      "-subj",
      "/C=US/ST=WA/L=WA/O=Network/OU=IT Department/CN=cocalc",
    ]);

    openssl.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Openssl process exited with code ${code}`));
      } else {
        resolve();
      }
    });
  });
}
