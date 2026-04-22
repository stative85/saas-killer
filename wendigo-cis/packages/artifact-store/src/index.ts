import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { config } from "@wendigo/config";

export interface ArtifactMeta {
  checksum: string;
  contentType: string;
}

export class ArtifactStore {
  async put(jobId: string, key: string, content: Buffer | string, contentType: string): Promise<string> {
    const storagePath = path.join(config.LOCAL_ARTIFACT_PATH, jobId, key);
    await fs.mkdir(path.dirname(storagePath), { recursive: true });
    
    const buffer = Buffer.isBuffer(content) ? content : Buffer.from(content);
    const checksum = crypto.createHash("sha256").update(buffer).digest("hex");
    
    await fs.writeFile(storagePath, buffer);
    return `local://${jobId}/${key}`; // v0 internal URI
  }

  async get(uri: string): Promise<Buffer> {
    const [_, pathPart] = uri.split("local://");
    const fullPath = path.join(config.LOCAL_ARTIFACT_PATH, pathPart);
    return fs.readFile(fullPath);
  }
}
