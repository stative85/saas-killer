import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

let jobCounter = 0;

// --- THE Crucible (IMPARTIAL JUDGE) ---
async function validate(job, patchType) {
    console.log(`[VALIDATOR] ⚔️ Commencing Crucible for ${job.id} (Mode: ${patchType})`);
    
    const workDir = path.join(process.cwd(), '.crucible', job.id);
    await fs.mkdir(workDir, { recursive: true });

    // Patch Library
    const patches = {
        'BAD': `
export function merge(target, source) {
    for (let key in source) {
        if (typeof source[key] === 'object') {
            if (!target[key]) target[key] = {};
            merge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}`,
        'GOOD': `
export function merge(target, source) {
    for (let key in source) {
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') continue;
        if (typeof source[key] === 'object' && source[key] !== null) {
            if (!target[key]) target[key] = {};
            merge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}`
    };

    const targetPath = path.join(workDir, 'target.js');
    await fs.writeFile(targetPath, patches[patchType]);

    // Hostile Invariant Test
    const testCode = `
import { merge } from './target.js';
const payload = JSON.parse('{"__proto__": {"polluted": "YES"}}');
const target = {};
try { merge(target, payload); } catch (e) {}
if (({}).polluted === 'YES') {
    console.error('[FATALITY] Object.prototype polluted!');
    process.exit(1);
} else {
    console.log('[SUCCESS] Prototype is clean.');
    process.exit(0);
}`;
    const testPath = path.join(workDir, 'test.js');
    await fs.writeFile(testPath, testCode);

    console.log(`[VALIDATOR] ⚡ Running Hostile Invariant...`);
    const result = spawnSync('node', [testPath], { encoding: 'utf-8' });
    console.log(result.stdout || result.stderr);

    return { success: result.status === 0, reason: result.status !== 0 ? 'PROTOTYPE_POLLUTION' : null };
}

// --- ORCHESTRATOR ---
async function advance(job, patchType) {
    console.log(`[ORCHESTRATOR] Job ${job.id} -> ${job.state}`);
    
    if (job.state === 'RECEIVED') {
        job.state = 'VALIDATING';
        const triage = await validate(job, patchType);
        
        if (!triage.success) {
            job.state = 'HUMAN_REVIEW_REQUIRED';
            console.error(`[CRUCIBLE] 💀 FATALITY: ${triage.reason}. Job ${job.id} REJECTED.\n`);
        } else {
            job.state = 'VALIDATED';
            console.log(`[CRUCIBLE] ✅ TRUTH ATTAINED. Job ${job.id} SURVIVED.\n`);
            advance(job, patchType);
        }
    } else if (job.state === 'VALIDATED') {
        job.state = 'PR_GENERATED';
        console.log(`[PR] Opening remediation branch: wendigo/sec-${job.id}\n`);
    }
}

// --- SERVER ---
const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/webhooks/snyk') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            const event = JSON.parse(body);
            const jobId = Math.random().toString(36).substring(7);
            // Alternate between BAD and GOOD for consecutive jobs
            const patchType = (jobCounter++ % 2 === 0) ? 'BAD' : 'GOOD';
            
            console.log(`\n[WENDIGO] ALERT CAPTURED: ${event.repository.name} (Assigned Patch: ${patchType})`);
            const job = { id: jobId, state: 'RECEIVED' };
            process.nextTick(() => advance(job, patchType));
            res.writeHead(202);
            res.end(JSON.stringify({ jobId }));
        });
    }
});

server.listen(3000, () => {
    console.log(`\n[WENDIGO-UNIFIED] BIDIRECTIONAL TRUTH ENGINE LIVE PORT 3000`);
    console.log(`[WENDIGO-UNIFIED] IMPARTIAL CRUCIBLE READY.\n`);
});
