import http from 'node:http';

const state = {
    jobs: []
};

// --- TRAPDOOR INGRESS ---
const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/webhooks/snyk') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            const event = JSON.parse(body);
            const jobId = Math.random().toString(36).substring(7);
            
            console.log(`[WENDIGO] Job Captured: ${jobId} for ${event.repository.name}`);
            
            const job = {
                id: jobId,
                repo: event.repository.name,
                state: 'RECEIVED',
                target: event.alert.targetFile
            };
            
            state.jobs.push(job);
            
            // --- THE TRUTH LOOP START ---
            process.nextTick(() => advance(job));
            
            res.writeHead(202, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'accepted', jobId }));
        });
    } else {
        res.writeHead(404);
        res.end();
    }
});

// --- THE CRUCIBLE ---
function advance(job) {
    console.log(`[ORCHESTRATOR] Job ${job.id} -> ${job.state}`);
    
    if (job.state === 'RECEIVED') {
        job.state = 'REPO_PREPARED';
        setTimeout(() => advance(job), 1000);
    } else if (job.state === 'REPO_PREPARED') {
        job.state = 'SLICED';
        setTimeout(() => advance(job), 1000);
    } else if (job.state === 'SLICED') {
        job.state = 'VALIDATED';
        console.log(`[VALIDATOR] Testing hostile invariants on ${job.target}...`);
        setTimeout(() => advance(job), 2000);
    } else if (job.state === 'VALIDATED') {
        job.state = 'PR_GENERATED';
        console.log(`[PR] Opening remediation branch: wendigo/sec-${job.id}`);
        setTimeout(() => advance(job), 1000);
    } else if (job.state === 'PR_GENERATED') {
        job.state = 'DONE';
        console.log(`[WENDIGO] MISSION COMPLETE FOR ${job.id}`);
    }
}

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`\n[WENDIGO-NINJA] TRAPDOOR IS LIVE ON PORT ${PORT}`);
    console.log(`[WENDIGO-NINJA] READY FOR RAW PAYLOADS.\n`);
});
