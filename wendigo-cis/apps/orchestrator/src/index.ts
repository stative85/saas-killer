import { JobState } from "@wendigo/contracts";
import { Queue } from "bullmq";

export class Orchestrator {
  private queueMap: Record<JobState, Queue>;

  constructor(redisUrl: string) {
    this.queueMap = {
      RECEIVED: new Queue("job.repo-prep", { connection: { url: redisUrl } }),
      REPO_PREPARED: new Queue("job.slice", { connection: { url: redisUrl } }),
      SLICED: new Queue("job.invariants", { connection: { url: redisUrl } }),
      INVARIANTS_COMPILED: new Queue("job.arena", { connection: { url: redisUrl } }),
      ARENA_COMPLETE: new Queue("job.validate", { connection: { url: redisUrl } }),
      VALIDATED: new Queue("job.pr", { connection: { url: redisUrl } }),
      // Terminal states
      PR_GENERATED: null as any,
      DONE: null as any,
      FAILED: null as any,
      HUMAN_REVIEW_REQUIRED: null as any
    };
  }

  async advanceJob(jobId: string, currentState: JobState): Promise<void> {
    const nextQueue = this.queueMap[currentState];
    if (!nextQueue) {
      console.log(`[ORCHESTRATOR] Job ${jobId} is in terminal state: ${currentState}`);
      return;
    }

    console.log(`[ORCHESTRATOR] Advancing Job ${jobId} from ${currentState} to next stage.`);
    await nextQueue.add("process", { jobId, state: currentState });
    
    // Update DB state here...
  }
}
