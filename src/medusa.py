#!/usr/bin/env python3
import sys
import json
import logging
import subprocess
import os
import argparse

# AGENTS.md PRIORITY -2.5: JEDER A2A Agent ruft LLMs AUSSCHLIESSLICH über die opencode CLI auf
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [MEDUSA] - %(message)s", datefmt="%H:%M:%S")

def call_llm(prompt: str, timeout: int = 180) -> str:
    """Ruft das LLM via opencode CLI ab (Priority -2.5 Mandate)"""
    try:
        # opencode run expects --format json
        result = subprocess.run(
            ["opencode", "run", prompt, "--model", "google/antigravity-gemini-3.1-pro", "--format", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        parts = []
        for line in result.stdout.splitlines():
            try:
                ev = json.loads(line)
                if ev.get("type") == "text":
                    parts.append(ev.get("part", {}).get("text", ""))
            except json.JSONDecodeError:
                pass
        return "".join(parts).strip()
    except subprocess.TimeoutExpired:
        logging.error("LLM Synthese-Timeout. Crucible Abbruch.")
        return ""
    except Exception as e:
        logging.error(f"LLM Aufruf fehlgeschlagen: {e}")
        return ""

def synthesize_mcp(target_api: str, description: str):
    """
    Software 3.0: Autonomous Skill Synthesis (ASS).
    Generiert einen kompletten Node.js MCP Server.
    """
    logging.info(f"⚡ NEURAL-BUS EVENT ERKANNT: [CapabilityGap]")
    logging.info(f"Target API: {target_api} | Context: {description}")
    logging.info("Start der autonomen MCP Synthese (Spawning Hephaestus-Subroutine)...")

    prompt = f"""
    Du bist A2A-SIN-Medusa, der Self-Extender-Agent. Dein Ziel ist es, einen vollständigen Model Context Protocol (MCP) Server in TypeScript/Node.js zu schreiben.
    
    ZIEL-API: {target_api}
    BESCHREIBUNG: {description}
    
    Schreibe den EXAKTEN, vollständigen Quellcode für die Datei 'index.ts', die einen voll funktionsfähigen MCP-Server bereitstellt, der diese API bedient. 
    Verwende das offizielle '@modelcontextprotocol/sdk/server/index.js' Paket.
    Definiere mindestens 2 nützliche Tools (z.B. read, write, search).
    Gib NUR den reinen Quellcode zurück, ohne Markdown-Blöcke oder Erklärungen. Beginne direkt mit 'import'.
    """

    logging.info("Sende Prompt an Multi-Model Adversarial Swarm (via opencode CLI)...")
    code = call_llm(prompt)

    if not code:
        logging.error("Synthese fehlgeschlagen (Kein Code zurückgegeben).")
        return

    # Clean up markdown if the LLM leaked it despite instructions
    if code.startswith("```typescript") or code.startswith("```ts"):
        code = code.split("\n", 1)[1]
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]

    # Speichern im Sandbox-Verzeichnis (The Crucible)
    sandbox_dir = os.path.join(os.path.dirname(__file__), f"../sandbox/mcp-{target_api.lower().replace(' ', '-')}")
    os.makedirs(sandbox_dir, exist_ok=True)
    
    file_path = os.path.join(sandbox_dir, "index.ts")
    with open(file_path, "w") as f:
        f.write(code.strip())

    logging.info(f"✅ Synthese erfolgreich! Code in Crucible Sandbox geschrieben: {file_path}")
    logging.info(f"Zeilen generiert: {len(code.splitlines())}")
    logging.info("Nächster Schritt (Simuliert): Firecracker MicroVM Test-Run & Registry Injection.")

def main():
    parser = argparse.ArgumentParser(description="A2A-SIN-Medusa (The MCP Factory)")
    parser.add_argument("--api", type=str, required=True, help="Der Name der fehlenden API (z.B. 'Spotify')")
    parser.add_argument("--desc", type=str, required=True, help="Beschreibung der gewünschten Fähigkeiten")
    
    args = parser.parse_args()
    synthesize_mcp(args.api, args.desc)

if __name__ == "__main__":
    main()
