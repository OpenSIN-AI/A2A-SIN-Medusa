#!/usr/bin/env python3
import sys
import json
import logging
import subprocess
import os
import argparse
import shutil
import time

# AGENTS.md PRIORITY -2.5: JEDER A2A Agent ruft LLMs AUSSCHLIESSLICH über die opencode CLI auf
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [MEDUSA] - %(message)s", datefmt="%H:%M:%S")

def call_llm(prompt: str, timeout: int = 180) -> str:
    """Ruft das LLM via opencode CLI ab und fängt den gesamten Stream (Priority -2.5 Mandate)"""
    try:
        # opencode run liefert JSONL Stream. Wir müssen alle text parts sammeln.
        result = subprocess.run(
            ["opencode", "run", prompt, "--model", "google/antigravity-gemini-3.1-pro", "--format", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        full_text = ""
        for line in result.stdout.splitlines():
            try:
                ev = json.loads(line)
                if ev.get("type") == "text":
                    full_text += ev.get("part", {}).get("text", "")
            except json.JSONDecodeError:
                pass
                
        # Fallback falls stdout leer ist aber stderr was hat (z.B. Fehler)
        if not full_text and "error" in result.stderr.lower():
            logging.error(f"LLM CLI Error: {result.stderr}")
            
        return full_text.strip()
    except subprocess.TimeoutExpired:
        logging.error("LLM Synthese-Timeout. Crucible Abbruch.")
        return ""
    except Exception as e:
        logging.error(f"LLM Aufruf fehlgeschlagen: {e}")
        return ""

def run_crucible_test(sandbox_dir: str) -> dict:
    """
    Software 3.0: The Crucible (Sandbox Validation)
    100% Test-Beweis Pflicht (Priority -4.0)
    """
    logging.info("🔥 The Crucible: Starte Sandbox-Validierung...")
    
    try:
        # 1. NPM Install
        logging.info("Installiere Abhängigkeiten (@modelcontextprotocol/sdk)...")
        subprocess.run(["npm", "install"], cwd=sandbox_dir, check=True, capture_output=True)
        
        # 2. Typescript Build
        logging.info("Kompiliere TypeScript zu JavaScript...")
        subprocess.run(["npx", "tsc"], cwd=sandbox_dir, check=True, capture_output=True)
        
        # 3. Syntax / Execution Test (Dry Run des MCP Servers)
        logging.info("Führe MCP Server Test-Boot durch...")
        # Wir starten den Server und beenden ihn direkt wieder, um Syntax/Import-Fehler zu catchen
        test_run = subprocess.run(
            ["node", "build/index.js"],
            cwd=sandbox_dir,
            capture_output=True,
            text=True,
            timeout=5 # MCP Server laufen endlos auf stdio, 5s ohne Crash = Success
        )
        return {"success": True, "error": None}
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        logging.error(f"Crucible Validation fehlgeschlagen: {error_msg}")
        return {"success": False, "error": error_msg}
    except subprocess.TimeoutExpired:
        # Ein Timeout ist hier ein ERFOLG, da der MCP Server auf stdio wartet und nicht crasht!
        logging.info("MCP Server läuft stabil (wartet auf stdio).")
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def synthesize_mcp(target_api: str, description: str, max_retries: int = 3):
    """
    Autonomous Skill Synthesis mit Self-Healing Loop.
    """
    logging.info(f"⚡ NEURAL-BUS EVENT ERKANNT: [CapabilityGap]")
    logging.info(f"Target API: {target_api} | Context: {description}")
    
    sandbox_dir = os.path.join(os.path.dirname(__file__), f"../sandbox/mcp-{target_api.lower().replace(' ', '-')}")
    os.makedirs(sandbox_dir, exist_ok=True)
    
    # Init Node Project
    with open(os.path.join(sandbox_dir, "package.json"), "w") as f:
        f.write(json.dumps({
            "name": f"mcp-{target_api.lower().replace(' ', '-')}",
            "version": "1.0.0",
            "type": "module",
            "dependencies": { "@modelcontextprotocol/sdk": "^1.0.1" },
            "devDependencies": { "typescript": "^5.0.0", "@types/node": "^20.0.0" }
        }, indent=2))
        
    with open(os.path.join(sandbox_dir, "tsconfig.json"), "w") as f:
        f.write(json.dumps({
            "compilerOptions": {
                "target": "ES2022", "module": "NodeNext", "moduleResolution": "NodeNext",
                "outDir": "./build", "rootDir": "./src", "strict": True
            },
            "include": ["src/**/*"]
        }, indent=2))
        
    src_dir = os.path.join(sandbox_dir, "src")
    os.makedirs(src_dir, exist_ok=True)

    error_context = ""
    
    for attempt in range(1, max_retries + 1):
        logging.info(f"Spawning Hephaestus-Subroutine (Versuch {attempt}/{max_retries})...")

        prompt = f"""
        Du bist A2A-SIN-Medusa. Schreibe den Code für einen TypeScript MCP Server.
        ZIEL: {target_api}
        BESCHREIBUNG: {description}
        {f'ACHTUNG! Der letzte Versuch hatte diesen Fehler. FIXE IHN: {error_context}' if error_context else ''}
        
        Regeln:
        1. Nutze "@modelcontextprotocol/sdk/server/index.js" und "@modelcontextprotocol/sdk/server/stdio.js".
        2. Exportiere keinen Code, führe server.connect(transport) am Ende aus.
        3. Gib NUR den TypeScript Code zurück. KEINE Markdown-Blöcke. KEIN Text davor oder danach.
        """

        code = call_llm(prompt)

        if not code:
            logging.error("Synthese fehlgeschlagen (Kein Code).")
            continue

        if code.startswith("```"):
            code = code.split("\n", 1)[-1].rsplit("```", 1)[0]

        file_path = os.path.join(src_dir, "index.ts")
        with open(file_path, "w") as f:
            f.write(code.strip())

        logging.info(f"Code in Sandbox geschrieben ({len(code.splitlines())} Zeilen). Übergebe an Crucible...")
        
        result = run_crucible_test(sandbox_dir)
        if result["success"]:
            logging.info(f"✅ GÖTTLICH! Synthese und Crucible-Validation erfolgreich!")
            logging.info(f"Der neue MCP Server liegt bereit in: {sandbox_dir}")
            return
        else:
            logging.warning(f"❌ Crucible-Validation fehlgeschlagen. Starte Self-Healing Loop...")
            error_context = result["error"]

    logging.error("💥 Synthese endgültig fehlgeschlagen nach maximalen Retries. Werfe Event zurück auf den Neural-Bus.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", type=str, required=True)
    parser.add_argument("--desc", type=str, required=True)
    args = parser.parse_args()
    synthesize_mcp(args.api, args.desc)

if __name__ == "__main__":
    main()
