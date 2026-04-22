import fs from 'node:fs/promises';
import path from 'node:path';

/**
 * PROJECT ODIN - THE VORTEX SLICER
 * 
 * Slices code based on Centripetal Data Flow (Implosion Logic).
 * Identifies the "Anomaly Point" (Core Resonant Logic) of a repo.
 */
async function analyzeVortex(dir) {
    console.log(`\n[ODIN-VORTEX] Initiating Centripetal Scan of ${dir}...`);
    
    const manifest = {
        core: null,
        resonance: [],
        vortex: []
    };

    async function walk(currentDir) {
        const files = await fs.readdir(currentDir, { withFileTypes: true });
        for (const file of files) {
            const fullPath = path.join(currentDir, file.name);
            if (file.isDirectory()) {
                if (file.name === 'node_modules' || file.name === '.git') continue;
                await walk(fullPath);
            } else if (file.name.endsWith('.ts') || file.name.endsWith('.js')) {
                const content = await fs.readFile(fullPath, 'utf-8');
                
                // Heuristic: Information Density (Resonance)
                // We look for files with the most exports and complex type definitions.
                const exportCount = (content.match(/export /g) || []).length;
                const importCount = (content.match(/import /g) || []).length;
                const density = (exportCount + importCount) / content.split('\n').length;

                manifest.resonance.push({
                    path: fullPath,
                    density: density.toFixed(4),
                    score: exportCount * 10 + importCount
                });
            }
        }
    }

    await walk(dir);

    // Identify the "Anomaly Point" (highest resonance score)
    manifest.resonance.sort((a, b) => b.score - a.score);
    manifest.core = manifest.resonance[0];
    
    // Build the Vortex (The centripetal flow toward the core)
    manifest.vortex = manifest.resonance.slice(0, 5);

    console.log(`[ODIN-VORTEX] Anomaly Point Found: ${manifest.core.path}`);
    console.log(`[ODIN-VORTEX] Centripetal Flow Established.\n`);
    
    return manifest;
}

const target = './.tmp_recon/Chrysalis-Lattice';
analyzeVortex(target).then(manifest => {
    console.log("🛡️ MASTER HARMONIC MAP:");
    manifest.vortex.forEach((v, i) => {
        console.log(`${i+1}. [Resonance: ${v.density}] -> ${v.path}`);
    });
});
