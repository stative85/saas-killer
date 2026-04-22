import { z } from "zod";

const ConfigSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string(),
  REDIS_URL: z.string(),
  ARTIFACT_STORAGE_TYPE: z.enum(["local", "s3"]).default("local"),
  LOCAL_ARTIFACT_PATH: z.string().default("./.artifacts"),
  GITHUB_APP_PRIVATE_KEY: z.string().optional(),
  GITHUB_APP_ID: z.string().optional(),
});

export const config = ConfigSchema.parse(process.env);
export type Config = z.infer<typeof ConfigSchema>;
