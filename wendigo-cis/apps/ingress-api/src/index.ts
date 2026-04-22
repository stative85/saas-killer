import express from "express";
import { TrapdoorEventSchema } from "@wendigo/contracts";

const app = express();
app.use(express.json());

app.post("/webhooks/snyk", async (req, res) => {
  try {
    // 1. Verify Signature (Logic to be added in security package)
    
    // 2. Normalize Payload
    const event = TrapdoorEventSchema.parse(req.body);
    
    // 3. Create Job and Enqueue (Logic to be added)
    console.log(`[INGRESS] Received security alert: ${event.alert.vulnId} for ${event.repository.name}`);
    
    res.status(202).json({ status: "accepted" });
  } catch (err) {
    console.error(`[INGRESS] Invalid payload:`, err);
    res.status(400).json({ error: "invalid_payload" });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`[WENDIGO] Ingress API listening on port ${PORT}`);
});
