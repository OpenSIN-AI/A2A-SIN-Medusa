#!/usr/bin/env python3
"""
A2A-SIN-Medusa — The Self-Extender
Resolves: OpenSIN-AI/A2A-SIN-Medusa#1 (NATS event subscription)
Resolves: OpenSIN-AI/A2A-SIN-Medusa#2 (Ouroboros memory integration)

Modes:
  python medusa.py --listen              # NATS daemon mode (production)
  python medusa.py --api NAME --desc X  # CLI mode (dev/test)
"""

import sys
import json
import logging
import subprocess
import os
import argparse
import asyncio
import hashlib
import shutil
from datetime import datetime
from typing import Optional

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../OpenSIN-Neural-Bus/sdk/python")
)
try:
    from ouroboros.memory import OuroborosDNA

    _OUROBOROS_AVAILABLE = True
except ImportError:
    _OUROBOROS_AVAILABLE = False

try:
    import nats

    _NATS_AVAILABLE = True
except ImportError:
    _NATS_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [MEDUSA] - %(message)s",
    datefmt="%H:%M:%S",
)

NATS_URL = os.environ.get("NATS_URL", "nats://92.5.60.87:4222")
NATS_AUTH_TOKEN = os.environ.get("NATS_AUTH_TOKEN", "")
SUBJECT_GAP = "opensin.capability.gap"
SUBJECT_RESOLVED = "opensin.capability.resolved"
SUBJECT_FAILED = "opensin.capability.failed"
AGENT_ID = "A2A-SIN-Medusa"

dna: Optional[OuroborosDNA] = None
if _OUROBOROS_AVAILABLE:
    dna_db = os.path.join(os.path.dirname(__file__), "../data/ouroboros_dna.sqlite")
    os.makedirs(os.path.dirname(dna_db), exist_ok=True)
    dna = OuroborosDNA(db_path=dna_db)
    logging.info("🧬 Ouroboros DNA Memory geladen.")
else:
    logging.warning("⚠️  Ouroboros SDK nicht gefunden — Memory deaktiviert.")


def call_llm(prompt: str, timeout: int = 180) -> str:
    try:
        result = subprocess.run(
            [
                "opencode",
                "run",
                prompt,
                "--model",
                "google/antigravity-gemini-3.1-pro",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        full_text = ""
        for line in result.stdout.splitlines():
            try:
                ev = json.loads(line)
                if ev.get("type") == "text":
                    full_text += ev.get("part", {}).get("text", "")
            except json.JSONDecodeError:
                pass
        if not full_text and result.stderr:
            logging.error(f"LLM CLI Error: {result.stderr[:200]}")
        return full_text.strip()
    except subprocess.TimeoutExpired:
        logging.error("LLM Timeout.")
        return ""
    except Exception as e:
        logging.error(f"LLM Fehler: {e}")
        return ""


def run_crucible(sandbox_dir: str) -> dict:
    logging.info("🔥 The Crucible: Starte Sandbox-Validierung...")
    try:
        subprocess.run(
            ["npm", "install"], cwd=sandbox_dir, check=True, capture_output=True
        )
        subprocess.run(["npx", "tsc"], cwd=sandbox_dir, check=True, capture_output=True)
        subprocess.run(
            ["node", "build/index.js"],
            cwd=sandbox_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {"success": True, "error": None}
    except subprocess.CalledProcessError as e:
        err = (
            e.stderr.decode("utf-8")
            if isinstance(e.stderr, bytes)
            else str(e.stderr or e)
        )
        logging.error(f"Crucible fehlgeschlagen: {err[:300]}")
        return {"success": False, "error": err}
    except subprocess.TimeoutExpired:
        logging.info("MCP Server läuft stabil (wartet auf stdio). ✅")
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_prompt(
    target_api: str, description: str, error_context: str, prior_lessons: list
) -> str:
    few_shot = ""
    if prior_lessons:
        few_shot = "\n\nFEW-SHOT LEKTIONEN AUS DEM OUROBOROS-GEDÄCHTNIS (nutze diese Muster):\n"
        for i, l in enumerate(prior_lessons[:3], 1):
            few_shot += (
                f"{i}. [{l.get('agent_id', '?')}]: {l.get('lesson_learned', '')}\n"
            )

    error_block = ""
    if error_context:
        error_block = f"\nACHTUNG! Letzter Versuch hatte diesen Fehler — FIXE IHN:\n{error_context}\n"

    return f"""Du bist A2A-SIN-Medusa. Schreibe den Code für einen TypeScript MCP Server.
ZIEL: {target_api}
BESCHREIBUNG: {description}
{few_shot}{error_block}
Regeln:
1. Nutze "@modelcontextprotocol/sdk/server/index.js" und "@modelcontextprotocol/sdk/server/stdio.js".
2. Exportiere keinen Code, führe server.connect(transport) am Ende aus.
3. Gib NUR den TypeScript Code zurück. KEINE Markdown-Blöcke. KEIN Text davor oder danach.
"""


def synthesize_mcp(target_api: str, description: str, max_retries: int = 3) -> dict:
    logging.info(f"⚡ CapabilityGap erkannt → API: {target_api} | {description}")

    prior_lessons = []
    if dna:
        prior_lessons = dna.recall_lessons(target_api, limit=3)
        if prior_lessons:
            logging.info(
                f"🧠 {len(prior_lessons)} Ouroboros-Lektionen für '{target_api}' abgerufen."
            )

    sandbox_dir = os.path.join(
        os.path.dirname(__file__),
        f"../sandbox/mcp-{target_api.lower().replace(' ', '-').replace('/', '-')}",
    )
    os.makedirs(sandbox_dir, exist_ok=True)

    with open(os.path.join(sandbox_dir, "package.json"), "w") as f:
        f.write(
            json.dumps(
                {
                    "name": f"mcp-{target_api.lower().replace(' ', '-')}",
                    "version": "1.0.0",
                    "type": "module",
                    "dependencies": {"@modelcontextprotocol/sdk": "^1.0.1"},
                    "devDependencies": {
                        "typescript": "^5.0.0",
                        "@types/node": "^20.0.0",
                    },
                },
                indent=2,
            )
        )

    with open(os.path.join(sandbox_dir, "tsconfig.json"), "w") as f:
        f.write(
            json.dumps(
                {
                    "compilerOptions": {
                        "target": "ES2022",
                        "module": "NodeNext",
                        "moduleResolution": "NodeNext",
                        "outDir": "./build",
                        "rootDir": "./src",
                        "strict": True,
                    },
                    "include": ["src/**/*"],
                },
                indent=2,
            )
        )

    src_dir = os.path.join(sandbox_dir, "src")
    os.makedirs(src_dir, exist_ok=True)

    error_context = ""
    for attempt in range(1, max_retries + 1):
        logging.info(f"🔨 Synthese-Versuch {attempt}/{max_retries}...")
        prompt = _build_prompt(target_api, description, error_context, prior_lessons)
        code = call_llm(prompt)

        if not code:
            logging.error("Kein Code generiert.")
            continue

        if code.startswith("```"):
            code = code.split("\n", 1)[-1].rsplit("```", 1)[0]

        with open(os.path.join(src_dir, "index.ts"), "w") as f:
            f.write(code.strip())

        logging.info(
            f"Code geschrieben ({len(code.splitlines())} Zeilen) → Crucible..."
        )
        result = run_crucible(sandbox_dir)

        if result["success"]:
            code_hash = hashlib.sha256(code.encode()).hexdigest()[:12]
            logging.info(f"✅ Crucible bestanden! hash={code_hash}")

            if dna:
                dna.register_capability(
                    capability=f"mcp-{target_api.lower().replace(' ', '-')}",
                    path=sandbox_dir,
                    agent=AGENT_ID,
                )
                dna.remember_lesson(
                    agent_id=AGENT_ID,
                    context=f"{target_api}: {description}",
                    lesson=f"Erfolgreicher Code-Pattern für {target_api} (Versuch {attempt}): "
                    f"Nutze @modelcontextprotocol/sdk, module:NodeNext, server.connect(transport). hash={code_hash}",
                    success_rate=1.0,
                )
                logging.info("🧬 Erfolg in Ouroboros DNA gespeichert.")

            return {
                "status": "passed",
                "api": target_api,
                "mcp_name": f"mcp-{target_api.lower().replace(' ', '-')}",
                "sandbox_dir": sandbox_dir,
                "code_hash": code_hash,
                "attempt": attempt,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logging.warning(
                f"❌ Crucible fehlgeschlagen (Versuch {attempt}). Self-Healing..."
            )
            error_context = result["error"] or ""

            if dna:
                dna.remember_lesson(
                    agent_id=AGENT_ID,
                    context=f"{target_api}: {description}",
                    lesson=f"FEHLER bei Versuch {attempt}: {error_context[:300]}",
                    success_rate=0.0,
                )

    logging.error("💥 Synthese endgültig fehlgeschlagen nach max. Retries.")
    if dna:
        dna.remember_lesson(
            agent_id=AGENT_ID,
            context=f"{target_api}: {description}",
            lesson=f"TOTAL FAIL nach {max_retries} Versuchen. Letzter Fehler: {error_context[:300]}",
            success_rate=0.0,
        )
    return {
        "status": "failed",
        "api": target_api,
        "error": error_context,
        "timestamp": datetime.now().isoformat(),
    }


async def nats_listener():
    if not _NATS_AVAILABLE:
        logging.error("nats-py nicht installiert. Führe: pip install nats-py")
        sys.exit(1)

    logging.info(f"🌐 Verbinde mit Neural-Bus NATS: {NATS_URL}")

    connect_opts = {"servers": [NATS_URL]}
    if NATS_AUTH_TOKEN:
        connect_opts["token"] = NATS_AUTH_TOKEN

    nc = await nats.connect(**connect_opts)
    js = nc.jetstream()

    logging.info(f"✅ NATS verbunden. Lausche auf Subject: {SUBJECT_GAP}")

    async def handle_gap(msg):
        try:
            event = json.loads(msg.data.decode())
            api = event.get("api", "unknown")
            desc = event.get("desc", "")
            requestor = event.get("requestor", "unknown")
            logging.info(f"📨 CapabilityGap Event von '{requestor}': api={api}")

            await msg.ack()

            result = synthesize_mcp(api, desc)

            reply_subject = (
                SUBJECT_RESOLVED if result["status"] == "passed" else SUBJECT_FAILED
            )
            await nc.publish(reply_subject, json.dumps(result).encode())
            logging.info(
                f"📤 Ergebnis publiziert auf {reply_subject}: {result['status']}"
            )

        except Exception as e:
            logging.error(f"Fehler beim Verarbeiten des Events: {e}")
            try:
                await msg.nak()
            except Exception:
                pass

    try:
        await js.subscribe(SUBJECT_GAP, cb=handle_gap, durable="medusa-worker")
        logging.info(
            "🎯 JetStream Subscription aktiv. Warte auf CapabilityGap Events..."
        )
    except Exception:
        await nc.subscribe(SUBJECT_GAP, cb=handle_gap)
        logging.info(
            "📡 Core NATS Subscription aktiv (kein JetStream). Warte auf Events..."
        )

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await nc.drain()
        logging.info("NATS Verbindung getrennt.")


def main():
    parser = argparse.ArgumentParser(description="A2A-SIN-Medusa Self-Extender")
    parser.add_argument(
        "--listen", action="store_true", help="NATS Daemon-Modus (production)"
    )
    parser.add_argument("--api", type=str, help="API Name (CLI-Modus)")
    parser.add_argument("--desc", type=str, help="Beschreibung (CLI-Modus)")
    args = parser.parse_args()

    if args.listen:
        logging.info("🚀 Medusa startet im NATS-Daemon-Modus...")
        asyncio.run(nats_listener())
    elif args.api and args.desc:
        result = synthesize_mcp(args.api, args.desc)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
